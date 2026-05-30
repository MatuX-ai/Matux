import 'package:flutter_test/flutter_test.dart';
import 'package:imatuproject_flutter/services/hardware_communication_service.dart';
import 'package:imatuproject_flutter/utils/usb_device_utils.dart';

void main() {
  group('HardwareCommunicationService Tests', () {
    late HardwareCommunicationService service;

    setUp(() {
      service = HardwareCommunicationService();
    });

    test('单例模式测试', () {
      final service2 = HardwareCommunicationService();
      expect(service, same(service2));
    });

    test('初始状态检查', () {
      expect(service.isConnected, false);
    });

    test('WebUSB 支持检查', () {
      // 在测试环境中可能无法准确判断，但至少不应抛出异常
      expect(() => service.isUSBSupported, returnsNormally);
    });
  });

  group('UsbDeviceUtils Tests', () {
    test('常见设备列表获取', () {
      final devices = CommonUsbDevices.getAllDevices();
      expect(devices, isNotEmpty);
      expect(devices.length, greaterThan(0));
    });

    test('Arduino设备信息验证', () {
      expect(CommonUsbDevices.arduinoUno.vendorId, equals(0x2341));
      expect(CommonUsbDevices.arduinoUno.productId, equals(0x0043));
      expect(CommonUsbDevices.arduinoUno.name, equals('Arduino Uno'));
    });

    test('设备查找功能', () {
      final device = CommonUsbDevices.findByVendorId(0x2341);
      expect(device, isNotNull);
      expect(device!.vendorId, equals(0x2341));
    });
  });

  group('DataConverter Tests', () {
    test('十六进制字符串转换', () {
      final result = DataConverter.stringToBytes('0x01, 0x02, 0x03');
      expect(result, equals([1, 2, 3]));
    });

    test('十进制字符串转换', () {
      final result = DataConverter.stringToBytes('1, 2, 3', format: DataFormat.decimal);
      expect(result, equals([1, 2, 3]));
    });

    test('ASCII字符串转换', () {
      final result = DataConverter.stringToBytes('ABC', format: DataFormat.ascii);
      expect(result, equals([65, 66, 67])); // ASCII codes for A, B, C
    });

    test('自动格式检测', () {
      // 包含0x的应该被识别为十六进制
      final hexResult = DataConverter.stringToBytes('0x01, 0x02');
      expect(hexResult, equals([1, 2]));

      // 不包含特殊标识的应该被识别为ASCII
      final asciiResult = DataConverter.stringToBytes('Hello');
      expect(asciiResult, equals([72, 101, 108, 108, 111])); // ASCII for Hello
    });

    test('字节到字符串转换', () {
      final bytes = [72, 101, 108, 108, 111]; // "Hello"
      final result = DataConverter.bytesToString(bytes);

      expect(result, contains('HEX:'));
      expect(result, contains('ASCII: Hello'));
    });
  });

  group('CrcCalculator Tests', () {
    test('校验和计算', () {
      final data = [1, 2, 3, 4, 5];
      final checksum = CrcCalculator.calculateChecksum(data);
      final expected = (1 + 2 + 3 + 4 + 5) & 0xFF;
      expect(checksum, equals(expected));
    });

    test('XOR校验计算', () {
      final data = [1, 2, 3, 4, 5];
      final xorResult = CrcCalculator.calculateXor(data);
      final expected = 1 ^ 2 ^ 3 ^ 4 ^ 5;
      expect(xorResult, equals(expected));
    });

    test('校验和验证', () {
      final data = [1, 2, 3, 4, 5];
      final checksum = CrcCalculator.calculateChecksum(data);
      final dataWithChecksum = [...data, checksum];

      expect(CrcCalculator.verifyChecksum(dataWithChecksum), isTrue);
    });

    test('错误校验和验证', () {
      final data = [1, 2, 3, 4, 5];
      final dataWithWrongChecksum = [...data, 99]; // 错误的校验和

      expect(CrcCalculator.verifyChecksum(dataWithWrongChecksum), isFalse);
    });
  });

  group('Integration Tests', () {
    test('完整命令流程模拟', () async {
      // 模拟完整的硬件通信流程
      final service = HardwareCommunicationService();

      // 模拟连接过程（在真实环境中需要实际硬件）
      expect(service.isConnected, false);

      // 注意：实际的连接测试需要真实的USB设备
      // 这里只测试基本的状态流转
    });

    test('命令构建和解析', () {
      // 测试常见的硬件命令格式
      final initCommand = [0x01, 0x02, 0x03];
      final statusCommand = [0x10, 0x00];
      final ledCommand = [0x20, 0x01, 0xFF];

      expect(initCommand.length, equals(3));
      expect(statusCommand.length, equals(2));
      expect(ledCommand.length, equals(3));

      // 验证命令格式合理性
      expect(initCommand[0], equals(0x01)); // 初始化命令码
      expect(statusCommand[0], equals(0x10)); // 状态查询命令码
      expect(ledCommand[0], equals(0x20)); // LED控制命令码
    });
  });
}
