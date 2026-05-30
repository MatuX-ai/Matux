import asyncio
from datetime import datetime
import json
import logging
from typing import Dict, List

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
import websockets

logger = logging.getLogger(__name__)


class WebRTCManager:
    """WebRTC实时通信管理器"""

    def __init__(self):
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.data_channels: Dict[str, any] = {}
        self.active_streams: Dict[str, List[MediaStreamTrack]] = {}
        self.sensor_data_cache: Dict[str, List[Dict]] = {}

    async def create_peer_connection(self, session_id: str) -> RTCPeerConnection:
        """创建新的WebRTC连接"""
        pc = RTCPeerConnection()
        self.peer_connections[session_id] = pc

        # 设置连接事件处理
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"连接状态变更 {session_id}: {pc.connectionState}")
            if pc.connectionState == "failed":
                await pc.close()
                self.cleanup_session(session_id)

        @pc.on("track")
        def on_track(track):
            logger.info(f"收到轨道 {session_id}: {track.kind}")
            if session_id not in self.active_streams:
                self.active_streams[session_id] = []
            self.active_streams[session_id].append(track)

        # 创建数据通道
        channel = pc.createDataChannel("sensor_data")

        @channel.on("open")
        def on_open():
            logger.info(f"数据通道打开 {session_id}")
            self.data_channels[session_id] = channel

        @channel.on("message")
        def on_message(message):
            self.handle_data_channel_message(session_id, message)

        return pc

    def handle_data_channel_message(self, session_id: str, message: str):
        """处理数据通道消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "sensor_data_request":
                self.send_sensor_data(session_id, data.get("sensor_types", []))
            elif message_type == "hardware_command":
                self.process_hardware_command(session_id, data)
            elif message_type == "ping":
                self.send_pong(session_id)

        except json.JSONDecodeError:
            logger.error(f"无效的JSON消息: {message}")
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")

    async def create_offer(self, session_id: str) -> str:
        """创建SDP Offer"""
        pc = await self.create_peer_connection(session_id)

        # 添加视频轨道（如果需要）
        # 这里可以根据需要添加摄像头轨道

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        return json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        )

    async def handle_answer(self, session_id: str, answer_sdp: str):
        """处理SDP Answer"""
        if session_id not in self.peer_connections:
            raise Exception("会话不存在")

        pc = self.peer_connections[session_id]
        answer = RTCSessionDescription(sdp=answer_sdp, type="answer")
        await pc.setRemoteDescription(answer)

    def send_sensor_data(self, session_id: str, sensor_types: List[str]):
        """发送传感器数据"""
        if session_id not in self.data_channels:
            return

        try:
            # 获取最新的传感器数据
            sensor_data = self.get_cached_sensor_data(sensor_types)

            message = {
                "type": "sensor_data",
                "data": sensor_data,
                "timestamp": datetime.now().isoformat(),
            }

            self.data_channels[session_id].send(json.dumps(message))

        except Exception as e:
            logger.error(f"发送传感器数据失败: {e}")

    def cache_sensor_data(self, session_id: str, data: Dict):
        """缓存传感器数据"""
        if session_id not in self.sensor_data_cache:
            self.sensor_data_cache[session_id] = []

        self.sensor_data_cache[session_id].append(
            {"data": data, "timestamp": datetime.now().isoformat()}
        )

        # 限制缓存大小
        if len(self.sensor_data_cache[session_id]) > 100:
            self.sensor_data_cache[session_id] = self.sensor_data_cache[session_id][
                -50:
            ]

    def get_cached_sensor_data(self, sensor_types: List[str]) -> List[Dict]:
        """获取缓存的传感器数据"""
        all_data = []
        for session_data in self.sensor_data_cache.values():
            all_data.extend(session_data[-10:])  # 获取最近10条数据

        # 按传感器类型过滤
        if sensor_types:
            filtered_data = [
                data
                for data in all_data
                if data.get("data", {}).get("sensor_type") in sensor_types
            ]
            return filtered_data
        else:
            return all_data[-20:]  # 返回最近20条数据

    def process_hardware_command(self, session_id: str, command_data: Dict):
        """处理硬件控制命令"""
        command = command_data.get("command")
        params = command_data.get("params", {})

        try:
            # 这里应该调用实际的硬件控制服务
            result = self.execute_hardware_command(command, params)

            # 发送响应
            if session_id in self.data_channels:
                response = {
                    "type": "command_response",
                    "command": command,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                }
                self.data_channels[session_id].send(json.dumps(response))

        except Exception as e:
            logger.error(f"执行硬件命令失败: {e}")
            self.send_error_response(session_id, command, str(e))

    def execute_hardware_command(self, command: str, params: Dict) -> Dict:
        """执行硬件命令（需要实现具体逻辑）"""
        # 这里应该集成实际的硬件控制逻辑
        logger.info(f"执行硬件命令: {command} 参数: {params}")

        # 模拟响应
        return {
            "status": "success",
            "message": f"命令 {command} 执行完成",
            "result_data": params,
        }

    def send_pong(self, session_id: str):
        """发送pong响应"""
        if session_id in self.data_channels:
            pong_message = {"type": "pong", "timestamp": datetime.now().isoformat()}
            self.data_channels[session_id].send(json.dumps(pong_message))

    def send_error_response(self, session_id: str, command: str, error: str):
        """发送错误响应"""
        if session_id in self.data_channels:
            error_message = {
                "type": "error",
                "command": command,
                "error": error,
                "timestamp": datetime.now().isoformat(),
            }
            self.data_channels[session_id].send(json.dumps(error_message))

    def cleanup_session(self, session_id: str):
        """清理会话资源"""
        # 关闭数据通道
        if session_id in self.data_channels:
            try:
                self.data_channels[session_id].close()
            except Exception:
                pass

            del self.data_channels[session_id]

        # 关闭PeerConnection
        if session_id in self.peer_connections:
            try:
                asyncio.create_task(self.peer_connections[session_id].close())
            except Exception:
                pass

            del self.peer_connections[session_id]

        # 清理流媒体轨道
        if session_id in self.active_streams:
            del self.active_streams[session_id]

        # 清理传感器数据缓存
        if session_id in self.sensor_data_cache:
            del self.sensor_data_cache[session_id]

        logger.info(f"会话 {session_id} 资源已清理")

    async def close_all_connections(self):
        """关闭所有连接"""
        session_ids = list(self.peer_connections.keys())
        for session_id in session_ids:
            await self.cleanup_session(session_id)


# WebSocket服务器用于信令
class SignalingServer:
    """WebRTC信令服务器"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.webrtc_manager = WebRTCManager()
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}

    async def handle_client(
        self, websocket: websockets.WebSocketServerProtocol, path: str
    ):
        """处理客户端连接"""
        client_id = str(id(websocket))
        self.clients[client_id] = websocket
        logger.info(f"新客户端连接: {client_id}")

        try:
            async for message in websocket:
                await self.process_message(client_id, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端断开连接: {client_id}")
        finally:
            del self.clients[client_id]
            await self.webrtc_manager.cleanup_session(client_id)

    async def process_message(self, client_id: str, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "create_offer":
                # 创建WebRTC Offer
                offer = await self.webrtc_manager.create_offer(client_id)
                await self.send_to_client(
                    client_id, {"type": "offer_created", "offer": offer}
                )

            elif message_type == "answer":
                # 处理Answer
                answer_sdp = data.get("sdp")
                await self.webrtc_manager.handle_answer(client_id, answer_sdp)
                await self.send_to_client(client_id, {"type": "connection_established"})

            elif message_type == "ice_candidate":
                # 处理 ICE 候选者（简化处理）
                pass

            elif message_type == "sensor_data":
                # 缓存传感器数据
                sensor_data = data.get("data", {})
                self.webrtc_manager.cache_sensor_data(client_id, sensor_data)

        except json.JSONDecodeError:
            logger.error(f"无效的JSON消息: {message}")
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
            await self.send_error(client_id, str(e))

    async def send_to_client(self, client_id: str, message: Dict):
        """发送消息给客户端"""
        if client_id in self.clients:
            try:
                await self.clients[client_id].send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                del self.clients[client_id]

    async def send_error(self, client_id: str, error: str):
        """发送错误消息"""
        await self.send_to_client(client_id, {"type": "error", "message": error})

    async def start_server(self):
        """启动信令服务器"""
        server = await websockets.serve(self.handle_client, self.host, self.port)
        logger.info(f"WebRTC信令服务器启动在 ws://{self.host}:{self.port}")
        await server.wait_closed()


# 使用示例
async def main():
    """主函数示例"""
    signaling_server = SignalingServer()
    await signaling_server.start_server()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
