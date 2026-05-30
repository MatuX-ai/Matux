"""
BACKEND-P1-008: 硬件连接验证单元测试

测试硬件代码解析、配置对比、综合评分等功能
确保硬件集成验证的准确性和公正性

测试覆盖:
- _parse_control_code(): 代码解析器
- _get_standard_hardware_config(): 标准配置查询
- _compare_hardware_configs(): 配置对比
- _calculate_hardware_score(): 综合评分
- _check_hardware_integration(): 集成验证

@author: AI Development Team
@version: 1.0.0
@date: 2026-03-05
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


class TestControlCodeParser:
    """代码解析器测试 (_parse_control_code)"""

    @pytest.fixture
    def task_orchestration_service(self):
        """创建任务编排服务实例"""
        from services.task_orchestration_service import TaskOrchestrationService

        mock_db = Mock()
        service = TaskOrchestrationService(db_session=mock_db)
        return service

    def test_parse_simple_pin_mode(self, task_orchestration_service):
        """测试简单的 pinMode 提取"""
        code = """
        void setup() {
            pinMode(D0, OUTPUT);  // Fan control
            pinMode(D1, INPUT);
            pinMode(A0, OUTPUT);  // Water pump control
        }
        
        void loop() {
            digitalWrite(D0, HIGH);  // Turn on fan
            digitalWrite(A0, HIGH);  // Turn on pump
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert result["valid"] is True
        assert "D0" in result["pins"]
        assert "D1" in result["pins"]
        assert "A0" in result["pins"]
        assert result["pins"]["D0"] == "OUTPUT"
        assert result["pins"]["D1"] == "INPUT"
        assert result["pins"]["A0"] == "OUTPUT"

    def test_parse_digital_write(self, task_orchestration_service):
        """测试 digitalWrite 提取"""
        code = """
        void loop() {
            digitalWrite(D0, HIGH);
            digitalWrite(D1, LOW);
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "D0" in result["pins"]
        assert "D1" in result["pins"]

    def test_parse_analog_read(self, task_orchestration_service):
        """测试 analogRead 提取"""
        code = """
        int value = analogRead(A0);
        int sensor = analogRead(A1);
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "A0" in result["pins"]
        assert "A1" in result["pins"]

    def test_parse_temperature_sensor(self, task_orchestration_service):
        """测试温度传感器识别"""
        code = """
        float temperature = readTemperature();
        if (temperature > 30) {
            // 温度过高
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "温度传感器" in result["sensors"]

    def test_parse_humidity_sensor(self, task_orchestration_service):
        """测试湿度传感器识别"""
        code = """
        int humidity = getHumidity();
        Serial.println(humidity);
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "湿度传感器" in result["sensors"]

    def test_parse_light_sensor(self, task_orchestration_service):
        """测试光照传感器识别"""
        code = """
        int light_level = analogRead(A0);
        // 光照强度检测
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "光照传感器" in result["sensors"]

    def test_parse_soil_moisture_sensor(self, task_orchestration_service):
        """测试土壤湿度传感器识别"""
        code = """
        int soil_moisture = analogRead(A2);
        if (soil_moisture < 300) {
            waterPump.on();
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "土壤湿度传感器" in result["sensors"]

    def test_parse_co2_sensor(self, task_orchestration_service):
        """测试 CO2 传感器识别"""
        code = """
        int co2_level = readCO2();
        Serial.print("CO2: ");
        Serial.println(co2_level);
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "CO2 传感器" in result["sensors"]

    def test_parse_fan_actuator(self, task_orchestration_service):
        """测试风扇执行器识别"""
        code = """
        void controlFan() {
            if (temperature > 30) {
                fan.on();
            }
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "风扇" in result["actuators"]

    def test_parse_pump_actuator(self, task_orchestration_service):
        """测试水泵执行器识别"""
        code = """
        void waterPlants() {
            pump.write(90);
            delay(1000);
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "水泵" in result["actuators"]

    def test_parse_led_actuator(self, task_orchestration_service):
        """测试 LED 灯执行器识别"""
        code = """
        void controlLight() {
            led_brightness = 255;
            analogWrite(LED_PIN, led_brightness);
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "LED 灯" in result["actuators"]

    def test_parse_i2c_protocol(self, task_orchestration_service):
        """测试 I2C 协议识别"""
        code = """
        #include <Wire.h>
        
        void setup() {
            Wire.begin();
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "I2C" in result["communication_protocols"]

    def test_parse_spi_protocol(self, task_orchestration_service):
        """测试 SPI 协议识别"""
        code = """
        #include <SPI.h>
        
        void setup() {
            SPI.begin();
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "SPI" in result["communication_protocols"]

    def test_parse_uart_protocol(self, task_orchestration_service):
        """测试 UART 协议识别"""
        code = """
        void setup() {
            Serial.begin(9600);
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "UART/Serial" in result["communication_protocols"]

    def test_parse_wifi_protocol(self, task_orchestration_service):
        """测试 WiFi 协议识别"""
        code = """
        #include <WiFi.h>
        
        void connectToWiFi() {
            WiFi.begin(ssid, password);
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert "WiFi/Ethernet" in result["communication_protocols"]

    def test_parse_complete_system(self, task_orchestration_service):
        """测试完整系统代码解析"""
        code = """
        #include <Wire.h>
        
        #define FAN_PIN D0
        #define PUMP_PIN D1
        #define TEMP_PIN A0
        
        void setup() {
            pinMode(FAN_PIN, OUTPUT);
            pinMode(PUMP_PIN, OUTPUT);
            pinMode(TEMP_PIN, INPUT);
            Wire.begin();
            Serial.begin(9600);
        }
        
        void loop() {
            float temperature = analogRead(TEMP_PIN);  // Read temperature sensor
            if (temperature > 30) {
                digitalWrite(FAN_PIN, HIGH);  // Turn on fan
            }
            digitalWrite(PUMP_PIN, HIGH);  // Turn on water pump
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert result["valid"] is True
        assert len(result["pins"]) >= 3
        assert len(result["sensors"]) >= 1
        assert len(result["actuators"]) >= 2
        assert len(result["communication_protocols"]) >= 2

    def test_parse_invalid_code_empty(self, task_orchestration_service):
        """测试空代码"""
        code = ""

        result = task_orchestration_service._parse_control_code(code)

        assert result["valid"] is False
        assert len(result["pins"]) == 0
        assert len(result["sensors"]) == 0
        assert len(result["actuators"]) == 0

    def test_parse_invalid_code_no_pins(self, task_orchestration_service):
        """测试无引脚配置的代码"""
        code = """
        void loop() {
            Serial.println("Hello");
        }
        """

        result = task_orchestration_service._parse_control_code(code)

        assert result["valid"] is False
        assert len(result["pins"]) == 0


class TestStandardHardwareConfig:
    """标准配置查询测试 (_get_standard_hardware_config)"""

    @pytest.fixture
    def task_orchestration_service(self):
        """创建任务编排服务实例"""
        from services.task_orchestration_service import TaskOrchestrationService

        mock_db = Mock()
        service = TaskOrchestrationService(db_session=mock_db)
        return service

    @pytest.mark.asyncio
    async def test_get_greenhouse_001_config(self, task_orchestration_service):
        """测试 greenhouse_001 任务配置"""
        config = await task_orchestration_service._get_standard_hardware_config(
            "greenhouse_001"
        )

        assert "required_pins" in config
        assert "required_sensors" in config
        assert "required_actuators" in config
        assert "required_protocols" in config
        assert "D0" in config["required_pins"]
        assert "温度传感器" in config["required_sensors"]
        assert "水泵" in config["required_actuators"]

    @pytest.mark.asyncio
    async def test_get_greenhouse_002_config(self, task_orchestration_service):
        """测试 greenhouse_002 任务配置"""
        config = await task_orchestration_service._get_standard_hardware_config(
            "greenhouse_002"
        )

        assert len(config["required_pins"]) >= 4
        assert len(config["required_sensors"]) >= 3
        assert len(config["required_actuators"]) >= 2
        assert "I2C" in config["required_protocols"]
        assert "SPI" in config["required_protocols"]

    @pytest.mark.asyncio
    async def test_get_default_config(self, task_orchestration_service):
        """测试默认配置"""
        config = await task_orchestration_service._get_standard_hardware_config(
            "unknown_task"
        )

        assert "required_pins" in config
        assert "required_sensors" in config
        assert "required_actuators" in config
        assert config["required_pins"] == ["D0", "D1"]


class TestHardwareConfigComparator:
    """配置对比测试 (_compare_hardware_configs)"""

    @pytest.fixture
    def task_orchestration_service(self):
        """创建任务编排服务实例"""
        from services.task_orchestration_service import TaskOrchestrationService

        mock_db = Mock()
        service = TaskOrchestrationService(db_session=mock_db)
        return service

    def test_compare_perfect_match(self, task_orchestration_service):
        """测试完全匹配的配置"""
        student_config = {
            "pins": {"D0": "OUTPUT", "D1": "OUTPUT", "A0": "INPUT"},
            "sensors": ["温度传感器", "湿度传感器"],
            "actuators": ["风扇", "水泵"],
            "communication_protocols": ["I2C"],
        }

        standard_config = {
            "required_pins": ["D0", "D1", "A0"],
            "required_sensors": ["温度传感器", "湿度传感器"],
            "required_actuators": ["风扇", "水泵"],
            "required_protocols": ["I2C"],
        }

        result = task_orchestration_service._compare_hardware_configs(
            student_config, standard_config
        )

        assert result["scores"]["pins"] == 100.0
        assert result["scores"]["sensors"] == 100.0
        assert result["scores"]["actuators"] == 100.0
        assert result["scores"]["protocols"] == 100.0
        assert len(result["suggestions"]) == 0

    def test_compare_missing_pins(self, task_orchestration_service):
        """测试缺少引脚"""
        student_config = {
            "pins": {"D0": "OUTPUT"},
            "sensors": ["温度传感器"],
            "actuators": ["风扇"],
            "communication_protocols": [],
        }

        standard_config = {
            "required_pins": ["D0", "D1", "A0"],
            "required_sensors": ["温度传感器"],
            "required_actuators": ["风扇"],
            "required_protocols": [],
        }

        result = task_orchestration_service._compare_hardware_configs(
            student_config, standard_config
        )

        assert result["scores"]["pins"] < 100.0
        assert "D1" in result["feedback"]["pins"]["missing"]
        assert "A0" in result["feedback"]["pins"]["missing"]
        assert any("引脚" in suggestion for suggestion in result["suggestions"])

    def test_compare_missing_sensors(self, task_orchestration_service):
        """测试缺少传感器"""
        student_config = {
            "pins": {"D0": "OUTPUT", "D1": "OUTPUT"},
            "sensors": ["温度传感器"],
            "actuators": ["风扇"],
            "communication_protocols": [],
        }

        standard_config = {
            "required_pins": ["D0", "D1"],
            "required_sensors": ["温度传感器", "湿度传感器", "光照传感器"],
            "required_actuators": ["风扇"],
            "required_protocols": [],
        }

        result = task_orchestration_service._compare_hardware_configs(
            student_config, standard_config
        )

        assert result["scores"]["sensors"] < 100.0
        assert "湿度传感器" in result["feedback"]["sensors"]["missing"]
        assert "光照传感器" in result["feedback"]["sensors"]["missing"]

    def test_compare_extra_pins(self, task_orchestration_service):
        """测试多余引脚"""
        student_config = {
            "pins": {"D0": "OUTPUT", "D1": "OUTPUT", "D2": "OUTPUT", "D3": "OUTPUT"},
            "sensors": ["温度传感器"],
            "actuators": ["风扇"],
            "communication_protocols": [],
        }

        standard_config = {
            "required_pins": ["D0", "D1"],
            "required_sensors": ["温度传感器"],
            "required_actuators": ["风扇"],
            "required_protocols": [],
        }

        result = task_orchestration_service._compare_hardware_configs(
            student_config, standard_config
        )

        assert result["scores"]["pins"] == 100.0  # 多出不扣分
        assert "D2" in result["feedback"]["pins"]["extra"]
        assert "D3" in result["feedback"]["pins"]["extra"]

    def test_compare_response_time_estimation(self, task_orchestration_service):
        """测试响应时间估算"""
        student_config = {
            "pins": {"D0": "OUTPUT", "D1": "OUTPUT"},
            "sensors": ["温度传感器"],
            "actuators": ["风扇"],
            "communication_protocols": [],
        }

        standard_config = {
            "required_pins": ["D0", "D1"],
            "required_sensors": ["温度传感器"],
            "required_actuators": ["风扇"],
            "required_protocols": [],
        }

        result = task_orchestration_service._compare_hardware_configs(
            student_config, standard_config
        )

        assert "response_time_ms" in result
        assert result["response_time_ms"] > 0


class TestHardwareScoreCalculator:
    """综合评分测试 (_calculate_hardware_score)"""

    @pytest.fixture
    def task_orchestration_service(self):
        """创建任务编排服务实例"""
        from services.task_orchestration_service import TaskOrchestrationService

        mock_db = Mock()
        service = TaskOrchestrationService(db_session=mock_db)
        return service

    def test_calculate_perfect_score(self, task_orchestration_service):
        """测试满分计算"""
        comparison_result = {
            "scores": {
                "pins": 100.0,
                "sensors": 100.0,
                "actuators": 100.0,
                "protocols": 100.0,
            }
        }

        score = task_orchestration_service._calculate_hardware_score(comparison_result)

        assert score == 100.0

    def test_calculate_partial_score(self, task_orchestration_service):
        """测试部分分数计算"""
        comparison_result = {
            "scores": {
                "pins": 80.0,
                "sensors": 60.0,
                "actuators": 90.0,
                "protocols": 70.0,
            }
        }

        score = task_orchestration_service._calculate_hardware_score(comparison_result)

        # 加权平均：80*0.3 + 60*0.3 + 90*0.25 + 70*0.15 = 24 + 18 + 22.5 + 10.5 = 75.0
        assert abs(score - 75.0) < 0.1

    def test_calculate_zero_score(self, task_orchestration_service):
        """测试零分计算"""
        comparison_result = {
            "scores": {"pins": 0.0, "sensors": 0.0, "actuators": 0.0, "protocols": 0.0}
        }

        score = task_orchestration_service._calculate_hardware_score(comparison_result)

        assert score == 0.0

    def test_calculate_empty_scores(self, task_orchestration_service):
        """测试空分数字典"""
        comparison_result = {"scores": {}}

        score = task_orchestration_service._calculate_hardware_score(comparison_result)

        assert score == 0.0


class TestHardwareIntegrationCheck:
    """集成验证测试 (_check_hardware_integration)"""

    @pytest.fixture
    def task_orchestration_service(self):
        """创建任务编排服务实例"""
        from services.task_orchestration_service import TaskOrchestrationService

        mock_db = Mock()
        service = TaskOrchestrationService(db_session=mock_db)
        return service

    @pytest.mark.asyncio
    async def test_check_valid_submission(self, task_orchestration_service):
        """测试有效提交"""
        control_code = """
        void setup() {
            pinMode(D0, OUTPUT);
            pinMode(A0, INPUT);
            Wire.begin();
        }
        
        void loop() {
            float temp = analogRead(A0);
            if (temp > 30) {
                digitalWrite(D0, HIGH);
            }
        }
        """

        result = await task_orchestration_service._check_hardware_integration(
            user_id=123, task_id="greenhouse_001", control_code=control_code
        )

        assert "code_valid" in result
        assert "hardware_connected" in result
        assert "stability_score" in result
        assert "detailed_feedback" in result
        assert "improvement_suggestions" in result

    @pytest.mark.asyncio
    async def test_check_invalid_submission_empty(self, task_orchestration_service):
        """测试无效提交（空代码）"""
        result = await task_orchestration_service._check_hardware_integration(
            user_id=123, task_id="greenhouse_001", control_code=""
        )

        assert result["code_valid"] is False

    @pytest.mark.asyncio
    async def test_check_with_error_handling(self, task_orchestration_service):
        """测试错误处理"""
        # 模拟异常情况
        with patch.object(
            task_orchestration_service,
            "_parse_control_code",
            side_effect=Exception("Test error"),
        ):
            result = await task_orchestration_service._check_hardware_integration(
                user_id=123, task_id="greenhouse_001", control_code="invalid code"
            )

            assert "error" in result or result["code_valid"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
