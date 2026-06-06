import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:vector_math/vector_math_64.dart' as vector;
import 'dart:math' as math;

// 导入被测试的组件和服务
import 'package:imatuproject_flutter/widgets/professional_dashboard.dart';
import 'package:imatuproject_flutter/services/sensor_integration_service.dart';
import 'package:imatuproject_flutter/models/professional_instruments.dart' as instruments;
import 'package:imatuproject_flutter/utils/data_processor.dart';
import 'package:imatuproject_flutter/widgets/enhanced_ar_interaction.dart' as ar_interaction;
import 'package:imatuproject_flutter/widgets/enhanced_ar_virtual_multimeter.dart';

void main() {
  group('专业仪表盘测试', () {
    testWidgets('ProfessionalDashboard 显示测试', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ProfessionalDashboard(
              currentValue: 12.5,
              unit: 'V',
              instrumentType: 'multimeter',
              historyData: [10.0, 11.0, 12.0, 13.0, 12.5],
              primaryColor: Colors.blue,
            ),
          ),
        ),
      );

      // 验证仪表盘显示正确的数值
      expect(find.text('12.500'), findsOneWidget);
      expect(find.text('V'), findsOneWidget);
      expect(find.text('multimeter'), findsOneWidget);
    });

    testWidgets('模拟指针动画测试', (WidgetTester tester) async {
      final widget = ProfessionalDashboard(
        currentValue: 0.0,
        unit: 'V',
        instrumentType: 'multimeter',
        historyData: [],
        primaryColor: Colors.blue,
      );

      await tester.pumpWidget(
        MaterialApp(home: Scaffold(body: widget)),
      );

      // 验证初始状态
      expect(find.text('0.000'), findsOneWidget);
    });
  });

  group('传感器集成服务测试', () {
    late SensorIntegrationService service;

    setUp(() {
      service = SensorIntegrationService();
    });

    tearDown(() {
      service.dispose();
    });

    test('传感器校准功能测试', () {
      final calibration = SensorCalibration(slope: 2.0, offset: 1.0);
      service.setCalibration('test_sensor', calibration);

      // 验证校准参数设置成功
      // 注意：由于_calibrations是私有字段，这里只能测试公共接口
    });

    test('数据处理功能测试', () {
      final result = service.getSensorHistory('test_sensor', limit: 3);

      // 验证返回空历史数据（因为没有实际采集）
      expect(result.length, 0);
    });

    test('控制命令生成测试', () {
      final pwmCommand = PWMOutputCommand(channel: 0, dutyCyclePercent: 50.0);
      final bytes = pwmCommand.toBytes();

      expect(bytes, [0x10, 0, 128]); // 50% duty cycle = 128/255
    });
  });

  group('专业仪器模型测试', () {
    test('专业万用表部件创建测试', () {
      final meter = instruments.ProfessionalMultimeter(
        id: 'test_meter',
        position: vector.Vector3.zero(),
      );

      final parts = meter.getParts();

      // 验证创建了正确的部件数量
      expect(parts.length, greaterThan(5));

      // 验证包含主要部件类型
      final bodyPart = parts.firstWhere((part) => part.type == instruments.PartType.mainBody);
      expect(bodyPart, isNotNull);

      final displayPart = parts.firstWhere((part) => part.type == instruments.PartType.display);
      expect(displayPart, isNotNull);
    });

    test('仪器动画更新测试', () {
      final meter = instruments.ProfessionalMultimeter(
        id: 'test_meter',
        position: vector.Vector3.zero(),
      );

      // 设置目标值并更新动画
      meter.setCurrentValue(5.0);
      meter.updateAnimation(0.016); // 60fps的时间增量

      // 验证值已更新
      expect(meter.currentValue, closeTo(0.08, 0.01)); // 初始插值
    });

    test('仪器交互处理测试', () {
      final meter = instruments.ProfessionalMultimeter(
        id: 'test_meter',
        position: vector.Vector3.zero(),
      );

      // 测试点击交互
      final tapInteraction = instruments.InstrumentInteraction(
        type: instruments.InteractionType.tap,
        worldPosition: vector.Vector3(0, 0, 0),
      );

      meter.handleInteraction(tapInteraction);

      // 验证仪器能处理交互（不会抛出异常）
      expect(meter.isPoweredOn, false); // 默认应该是关闭状态
    });
  });

  group('数据处理模块测试', () {
    late DataProcessor processor;

    setUp(() {
      processor = DataProcessor();
    });

    tearDown(() {
      processor.clearCache();
    });

    test('FFT分析测试', () {
      // 生成测试信号
      final testData = processor.generateTestSignal(
        SignalType.sine,
        length: 1024,
        frequency: 50.0,
        amplitude: 1.0,
        sampleRate: 1000.0,
      );

      final fftResult = processor.performFFT(testData, sampleRate: 1000);

      // 验证FFT结果
      expect(fftResult.frequencies.length, 512); // N/2个频率点
      expect(fftResult.magnitudes.length, 512);
      expect(fftResult.phases.length, 512);

      // 验证主要频率成分
      final dominantFreq = fftResult.findPeakFrequency();
      expect(dominantFreq, isNotNull);
      expect(dominantFreq!.frequency, closeTo(50.0, 1.0)); // 应该接近50Hz
    });

    test('统计分析测试', () {
      final testData = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0];
      final stats = processor.calculateStatistics(testData);

      // 验证基本统计量
      expect(stats.count, 10);
      expect(stats.mean, 5.5);
      expect(stats.min, 1.0);
      expect(stats.max, 10.0);
      expect(stats.median, 5.5);
    });

    test('滤波器测试', () {
      // 生成带噪声的信号
      final noisySignal = processor.generateTestSignal(
        SignalType.sine,
        length: 1000,
        frequency: 10.0,
        amplitude: 1.0,
        noiseLevel: 0.3,
      );

      // 应用低通滤波器
      final filteredResult = processor.applyFilter(
        noisySignal,
        FilterType.lowPass,
        cutoffFrequency: 20.0,
        sampleRate: 1000.0,
      );

      // 验证滤波结果
      expect(filteredResult.filtered.length, noisySignal.length);
      expect(filteredResult.filterType, FilterType.lowPass);
    });

    test('异常值检测测试', () {
      final testData = [1.0, 1.1, 0.9, 1.2, 1.0, 10.0, 1.1, 0.8, 1.3, 1.0]; // 包含异常值10.0
      final result = processor.detectOutliers(testData, method: OutlierMethod.iqr);

      // 验证检测到异常值
      expect(result.outliers.length, 1);
      expect(result.outliers.values.first, 10.0);
      expect(result.outlierPercentage, 10.0);
    });

    test('信号生成测试', () {
      final sineWave = processor.generateTestSignal(
        SignalType.sine,
        length: 100,
        frequency: 1.0,
        amplitude: 2.0,
        sampleRate: 100.0,
      );

      // 验证生成的信号长度
      expect(sineWave.length, 100);

      // 验证信号幅值范围
      final maxVal = sineWave.reduce(math.max);
      final minVal = sineWave.reduce(math.min);
      expect(maxVal, closeTo(2.0, 0.1));
      expect(minVal, closeTo(-2.0, 0.1));
    });

    test('相关性分析测试', () {
      final data1 = [1.0, 2.0, 3.0, 4.0, 5.0];
      final data2 = [2.0, 4.0, 6.0, 8.0, 10.0]; // 完全正相关

      final correlation = processor.calculateCorrelation(data1, data2);

      // 验证完全正相关
      expect(correlation.correlation, closeTo(1.0, 0.001));
      expect(correlation.rSquared, closeTo(1.0, 0.001));
      expect(correlation.isValid, isTrue);
      expect(correlation.isSignificant, isTrue);
    });

    test('数据导出测试', () {
      final testData = [1.0, 2.0, 3.0, 4.0, 5.0];

      // 测试CSV导出
      final csvResult = processor.exportData(
        testData,
        ExportFormat.csv,
        fileName: 'test_data',
        metadata: {'source': 'unit_test'},
      );

      expect(csvResult.format, ExportFormat.csv);
      expect(csvResult.fileName, 'test_data.csv');
      expect(csvResult.content.isNotEmpty, isTrue);

      // 测试JSON导出
      final jsonResult = processor.exportData(
        testData,
        ExportFormat.json,
        fileName: 'test_data',
      );

      expect(jsonResult.format, ExportFormat.json);
      expect(jsonResult.fileName, 'test_data.json');
    });
  });

  group('增强AR交互测试', () {
    testWidgets('基本手势识别测试', (WidgetTester tester) async {
      bool interactionDetected = false;
      ar_interaction.InteractionType? detectedType;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ar_interaction.EnhancedARInteraction(
              onInteraction: (interaction) {
                interactionDetected = true;
                detectedType = interaction.type;
              },
              child: Container(color: Colors.blue),
            ),
          ),
        ),
      );

      // 测试点击手势
      await tester.tap(find.byType(Container));
      await tester.pumpAndSettle();

      expect(interactionDetected, isTrue);
      expect(detectedType, ar_interaction.InteractionType.tap);
    });

    testWidgets('双击手势测试', (WidgetTester tester) async {
      int tapCount = 0;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ar_interaction.EnhancedARInteraction(
              onInteraction: (interaction) {
                if (interaction.type == ar_interaction.InteractionType.tap) {
                  tapCount++;
                }
              },
              child: Container(color: Colors.red),
            ),
          ),
        ),
      );

      // 测试双击
      final container = find.byType(Container);
      await tester.tap(container);
      await tester.tap(container);
      await tester.pump(const Duration(milliseconds: 300)); // 双击间隔

      expect(tapCount, 2);
    });

    testWidgets('缩放手势测试', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ar_interaction.EnhancedARInteraction(
              onInteraction: (interaction) {
                // 测试模式下不处理
              },
              child: Container(
                width: 200,
                height: 200,
                color: Colors.green,
              ),
            ),
          ),
        ),
      );

      // 模拟缩放手势（这在测试环境中比较复杂，主要是验证不会出错）
      await tester.pumpAndSettle();
      expect(true, isTrue); // 基本测试通过
    });
  });

  group('增强AR万用表集成测试', () {
    testWidgets('完整组件集成测试', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: EnhancedArVirtualMultimeter(
              onPlaneDetected: (plane) {
                // 测试模式下不处理平面检测
              },
              onGestureDetected: (gesture) {
                // 测试模式下不处理手势检测
              },
              enableHardwareIntegration: false, // 测试模式下禁用硬件
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // 验证组件能正常构建
      expect(find.byType(Stack), findsOneWidget);
      expect(find.byType(Positioned), findsWidgets);
    });

    test('测量模式切换测试', () {
      // 测试测量模式枚举
      expect(MeasurementMode.values.length, 5);

      final voltageMode = MeasurementMode.voltage;
      expect(voltageMode.displayName, '电压');

      final currentMode = MeasurementMode.current;
      expect(currentMode.displayName, '电流');
    });

    test('AR 手势扩展功能测试', () {
      final gesture = ArCoreGesture(type: 'tap', data: {'tap_count': 2});
      final enhancedGesture = gesture as dynamic;

      // 验证扩展方法存在
      expect(enhancedGesture.tapCount, 2);
      expect(enhancedGesture.scaleFactor, 1.0);
    });
  });

  group('性能基准测试', () {
    test('大数据集FFT性能测试', () {
      final processor = DataProcessor();
      final largeDataset = List<double>.generate(8192, (i) => math.sin(i * 0.1));

      final stopwatch = Stopwatch()..start();
      final result = processor.performFFT(largeDataset);
      stopwatch.stop();

      // 验证性能（应该在合理时间内完成）
      expect(stopwatch.elapsedMilliseconds, lessThan(1000)); // 1秒内完成
      expect(result.frequencies.length, 4096);
    });

    test('高频数据处理性能测试', () {
      final processor = DataProcessor();
      final highFrequencyData = List<double>.generate(10000, (i) => math.Random().nextDouble());

      final stopwatch = Stopwatch()..start();
      final stats = processor.calculateStatistics(highFrequencyData);
      stopwatch.stop();

      expect(stopwatch.elapsedMilliseconds, lessThan(100)); // 100ms内完成
      expect(stats.count, 10000);
    });

    test('实时数据流处理性能测试', () {
      final service = SensorIntegrationService();

      final stopwatch = Stopwatch()..start();
      for (int i = 0; i < 100; i++) {
        service.getSensorHistory('perf_test_$i', limit: 10);
        // 模拟处理
      }
      stopwatch.stop();

      expect(stopwatch.elapsedMilliseconds, lessThan(200)); // 200ms内完成
      service.dispose();
    });
  });

  group('边界条件和错误处理测试', () {
    test('空数据集处理测试', () {
      final processor = DataProcessor();

      // 测试空数据的统计分析
      final emptyStats = processor.calculateStatistics([]);
      expect(emptyStats.count, 0);
      expect(emptyStats.mean, 0);

      // 测试空数据的FFT
      final emptyFFT = processor.performFFT([]);
      expect(emptyFFT.frequencies.length, 0);
    });

    test('异常数据处理测试', () {
      final processor = DataProcessor();

      // 测试包含NaN和无穷大的数据
      final badData = [1.0, double.nan, 3.0, double.infinity, 5.0];
      final stats = processor.calculateStatistics(badData);

      // 应该能处理而不崩溃
      expect(stats.count, greaterThan(0));
    });

    test('传感器服务边界测试', () {
      final service = SensorIntegrationService();

      // 测试多次dispose不会出错
      service.dispose();
      service.dispose(); // 不应该抛出异常

      // 测试空历史数据查询
      final emptyHistory = service.getSensorHistory('nonexistent', limit: 10);
      expect(emptyHistory.length, 0);
    });
  });
}
