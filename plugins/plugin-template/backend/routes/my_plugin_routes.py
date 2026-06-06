"""
我的插件 - 后端路由

这是一个示例路由文件，展示如何创建插件的后端 API。
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()


# ==================== 数据模型 ====================

class MyPluginRequest(BaseModel):
    """请求模型"""
    name: str
    value: Optional[str] = None


class MyPluginResponse(BaseModel):
    """响应模型"""
    success: bool
    message: str
    data: Optional[dict] = None


# ==================== API 端点 ====================

@router.get("/hello", response_model=MyPluginResponse)
async def hello_world():
    """
    示例端点：Hello World
    
    Returns:
        MyPluginResponse: 欢迎消息
    """
    return MyPluginResponse(
        success=True,
        message="Hello from my plugin!",
        data={"version": "1.0.0"}
    )


@router.post("/process", response_model=MyPluginResponse)
async def process_data(request: MyPluginRequest):
    """
    示例端点：处理数据
    
    Args:
        request: 请求数据
    
    Returns:
        MyPluginResponse: 处理结果
    """
    try:
        # 处理逻辑
        result = {
            "name": request.name,
            "value": request.value,
            "processed": True,
        }
        
        return MyPluginResponse(
            success=True,
            message="数据处理成功",
            data=result
        )
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"处理失败: {str(err)}"
        )


@router.get("/items", response_model=List[MyPluginResponse])
async def get_items(limit: int = 10, offset: int = 0):
    """
    示例端点：获取列表
    
    Args:
        limit: 返回数量限制
        offset: 偏移量
    
    Returns:
        List[MyPluginResponse]: 项目列表
    """
    # 模拟数据
    items = []
    for i in range(offset, offset + limit):
        items.append(MyPluginResponse(
            success=True,
            message=f"Item {i}",
            data={"id": i, "name": f"Item {i}"}
        ))
    
    return items


@router.get("/health")
async def health_check():
    """
    健康检查端点
    
    Returns:
        dict: 健康状态
    """
    return {
        "status": "healthy",
        "plugin": "my-plugin",
        "version": "1.0.0"
    }
