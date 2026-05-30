/// 加密工具类测试
library;

import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:skill_wallet_sdk/src/utils/crypto_utils.dart';
import 'package:logger/logger.dart';

void main() {
  final logger = Logger();

  group('CryptoUtils Ed25519 测试', () {
    test('生成密钥对并正确派生公钥', () async {
      // 生成密钥对
      final keyPair = await CryptoUtils.generateEd25519KeyPair();

      expect(keyPair.containsKey('privateKey'), isTrue);
      expect(keyPair.containsKey('publicKey'), isTrue);

      // 验证密钥长度
      final privateKeyBytes = base64Decode(keyPair['privateKey']!);
      final publicKeyBytes = base64Decode(keyPair['publicKey']!);

      // Ed25519 私钥应该是 64 字节（种子 + 公钥）
      expect(privateKeyBytes.length, equals(64));
      // Ed25519 公钥应该是 32 字节
      expect(publicKeyBytes.length, equals(32));

      logger.d('私钥长度：${privateKeyBytes.length}');
      logger.d('公钥长度：${publicKeyBytes.length}');
      logger.d('私钥：${keyPair['privateKey']}');
      logger.d('公钥：${keyPair['publicKey']}');
    });

    test('签名和验证', () async {
      // 生成密钥对
      final keyPair = await CryptoUtils.generateEd25519KeyPair();
      final privateKey = keyPair['privateKey']!;
      final publicKey = keyPair['publicKey']!;

      // 要签名的数据
      final data = 'Hello, World!';

      // 签名
      final signature = await CryptoUtils.signWithEd25519(privateKey, data);
      expect(signature.isNotEmpty, isTrue);

      logger.d('原始数据：$data');
      logger.d('签名：$signature');

      // 验证签名 - 正确的情况
      final isValid = await CryptoUtils.verifyWithEd25519(
        publicKey,
        data,
        signature,
      );
      expect(isValid, isTrue);

      // 验证签名 - 数据被篡改的情况
      final tamperedData = 'Hello, World!!'; // 注意多了一个感叹号
      final isTamperedValid = await CryptoUtils.verifyWithEd25519(
        publicKey,
        tamperedData,
        signature,
      );
      expect(isTamperedValid, isFalse);

      // 验证签名 - 使用错误的公钥
      final wrongKeyPair = await CryptoUtils.generateEd25519KeyPair();
      final wrongPublicKey = wrongKeyPair['publicKey']!;
      final isWrongKeyValid = await CryptoUtils.verifyWithEd25519(
        wrongPublicKey,
        data,
        signature,
      );
      expect(isWrongKeyValid, isFalse);
    });

    test('多次生成不同的密钥对', () async {
      final keyPair1 = await CryptoUtils.generateEd25519KeyPair();
      final keyPair2 = await CryptoUtils.generateEd25519KeyPair();

      // 每次生成的密钥对应该不同
      expect(keyPair1['privateKey'], isNot(equals(keyPair2['privateKey'])));
      expect(keyPair1['publicKey'], isNot(equals(keyPair2['publicKey'])));
    });
  });

  group('CryptoUtils DID 签名验证测试', () {
    test('完整的 DID 签名验证流程', () async {
      // 1. 生成颁发者密钥对
      final issuerKeyPair = await CryptoUtils.generateEd25519KeyPair();
      final issuerPrivateKey = issuerKeyPair['privateKey']!;
      final issuerPublicKey = issuerKeyPair['publicKey']!;

      // 2. 创建 DID 文档（简化版本）
      final didDocument = {
        '@context': [
          'https://www.w3.org/ns/did/v1',
          'https://w3id.org/security/suites/ed25519-2020/v1'
        ],
        'id': 'did:example:issuer123',
        'verificationMethod': [
          {
            'id': 'did:example:issuer123#keys-1',
            'type': 'Ed25519VerificationKey2020',
            'controller': 'did:example:issuer123',
            'publicKeyBase64': issuerPublicKey,
          }
        ],
        'assertionMethod': ['did:example:issuer123#keys-1'],
      };

      // 3. 要签名的数据（凭证）
      final credentialData = '{"name":"张三","skill":"区块链开发"}';

      // 4. 使用私钥签名
      final signature = await CryptoUtils.signWithEd25519(
        issuerPrivateKey,
        credentialData,
      );

      logger.d('DID 文档：$didDocument');
      logger.d('凭证数据：$credentialData');
      logger.d('签名：$signature');

      // 5. 验证签名
      final isValid = await CryptoUtils.verifyDidSignature(
        didDocument: didDocument,
        data: credentialData,
        signature: signature,
        verificationMethodId: 'did:example:issuer123#keys-1',
      );

      expect(isValid, isTrue);
    });

    test('DID 文档中找不到验证方法时返回 false', () async {
      final keyPair = await CryptoUtils.generateEd25519KeyPair();
      final privateKey = keyPair['privateKey']!;

      final didDocument = {
        '@context': ['https://www.w3.org/ns/did/v1'],
        'id': 'did:example:issuer456',
        'verificationMethod': [
          {
            'id': 'did:example:issuer456#keys-1',
            'type': 'Ed25519VerificationKey2020',
            'controller': 'did:example:issuer456',
            'publicKeyBase64': keyPair['publicKey']!,
          }
        ],
      };

      final data = 'Test data';
      final signature = await CryptoUtils.signWithEd25519(privateKey, data);

      // 使用错误的 verificationMethodId
      final isValid = await CryptoUtils.verifyDidSignature(
        didDocument: didDocument,
        data: data,
        signature: signature,
        verificationMethodId: 'did:example:issuer456#keys-999', // 不存在的 ID
      );

      expect(isValid, isFalse);
    });

    test('数据被篡改时验证失败', () async {
      final keyPair = await CryptoUtils.generateEd25519KeyPair();
      final privateKey = keyPair['privateKey']!;
      final publicKey = keyPair['publicKey']!;

      final didDocument = {
        '@context': ['https://www.w3.org/ns/did/v1'],
        'id': 'did:example:issuer789',
        'verificationMethod': [
          {
            'id': 'did:example:issuer789#keys-1',
            'type': 'Ed25519VerificationKey2020',
            'controller': 'did:example:issuer789',
            'publicKeyBase64': publicKey,
          }
        ],
        'assertionMethod': ['did:example:issuer789#keys-1'],
      };

      final originalData = 'Original data';
      final signature = await CryptoUtils.signWithEd25519(privateKey, originalData);

      // 使用篡改后的数据验证
      final tamperedData = 'Tampered data';
      final isValid = await CryptoUtils.verifyDidSignature(
        didDocument: didDocument,
        data: tamperedData, // 被篡改的数据
        signature: signature,
        verificationMethodId: 'did:example:issuer789#keys-1',
      );

      expect(isValid, isFalse);
    });

    test('支持 JWK 格式的公钥', () async {
      final keyPair = await CryptoUtils.generateEd25519KeyPair();
      final privateKey = keyPair['privateKey']!;
      final publicKeyBytes = base64Decode(keyPair['publicKey']!);

      // 将公钥转换为 Base64Url 编码（JWK 格式）
      String base64UrlEncode(Uint8List bytes) {
        return base64Encode(bytes)
            .replaceAll('+', '-')
            .replaceAll('/', '_')
            .replaceAll('=', '');
      }

      final didDocument = {
        '@context': ['https://www.w3.org/ns/did/v1'],
        'id': 'did:example:jwk-test',
        'verificationMethod': [
          {
            'id': 'did:example:jwk-test#keys-1',
            'type': 'JsonWebKey2020',
            'controller': 'did:example:jwk-test',
            'publicKeyJwk': {
              'kty': 'OKP',
              'crv': 'Ed25519',
              'x': base64UrlEncode(publicKeyBytes),
            },
          }
        ],
        'assertionMethod': ['did:example:jwk-test#keys-1'],
      };

      final data = 'JWK format test';
      final signature = await CryptoUtils.signWithEd25519(privateKey, data);

      final isValid = await CryptoUtils.verifyDidSignature(
        didDocument: didDocument,
        data: data,
        signature: signature,
        verificationMethodId: 'did:example:jwk-test#keys-1',
      );

      expect(isValid, isTrue);
    });
  });
}
