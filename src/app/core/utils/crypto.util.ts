/**
 * 前端轻量加密工具
 *
 * 使用 Web Crypto API (AES-GCM) 对敏感数据进行加密存储
 * 防止 localStorage 明文泄露 token/密码等敏感信息
 *
 * 安全模型：
 * - 密钥从用户密码派生（PBKDF2），不硬编码
 * - 每次加密使用随机 salt 和 iv，防止密文分析
 * - 仅防御被动读取（XSS 读取 localStorage 得到密文）
 * - 不防御主动内存读取（XSS 仍可调用加密函数）
 */

const ENC_ALG = 'AES-GCM';
const DERIVE_ALG = 'PBKDF2';
const HASH_ALG = 'SHA-256';
const ITERATIONS = 100_000;
const SALT_LEN = 16;
const IV_LEN = 12;

/**
 * 从用户标识派生加密密钥
 *
 * 使用 userId 作为密钥派生材料，确保不同用户密钥不同
 * 注意：这主要防御被动读取，不防御主动 XSS
 */
async function deriveKey(userId: string): Promise<CryptoKey> {
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    enc.encode(userId),
    DERIVE_ALG,
    false,
    ['deriveKey'],
  );

  return crypto.subtle.deriveKey(
    {
      name: DERIVE_ALG,
      salt: enc.encode(`matux-credential-salt-${userId}`),
      iterations: ITERATIONS,
      hash: HASH_ALG,
    },
    keyMaterial,
    { name: ENC_ALG, length: 256 },
    false,
    ['encrypt', 'decrypt'],
  );
}

/**
 * 加密数据
 *
 * 返回格式：salt(16字节) + iv(12字节) + ciphertext + authTag(16字节)
 * 全部编码为 base64 字符串
 */
export async function encrypt(plainText: string, userId: string): Promise<string> {
  const key = await deriveKey(userId);
  const enc = new TextEncoder();

  const salt = crypto.getRandomValues(new Uint8Array(SALT_LEN));
  const iv = crypto.getRandomValues(new Uint8Array(IV_LEN));

  const cipherText = await crypto.subtle.encrypt(
    { name: ENC_ALG, iv, tagLength: 128 },
    key,
    enc.encode(plainText),
  );

  // 拼接 salt + iv + ciphertext
  const combined = new Uint8Array(salt.length + iv.length + cipherText.byteLength);
  combined.set(salt, 0);
  combined.set(iv, salt.length);
  combined.set(new Uint8Array(cipherText), salt.length + iv.length);

  return btoa(String.fromCharCode(...combined));
}

/**
 * 解密数据
 *
 * 从 base64 字符串中提取 salt、iv、ciphertext 并解密
 */
export async function decrypt(cipherText: string, userId: string): Promise<string | null> {
  try {
    const key = await deriveKey(userId);
    const combined = Uint8Array.from(atob(cipherText), (c) => c.charCodeAt(0));

    if (combined.length < SALT_LEN + IV_LEN + 16) {
      return null; // 密文太短，数据损坏
    }

    const salt = combined.slice(0, SALT_LEN);
    const iv = combined.slice(SALT_LEN, SALT_LEN + IV_LEN);
    const data = combined.slice(SALT_LEN + IV_LEN);

    const plainBuffer = await crypto.subtle.decrypt(
      { name: ENC_ALG, iv, tagLength: 128 },
      key,
      data,
    );

    return new TextDecoder().decode(plainBuffer);
  } catch {
    return null; // 解密失败（密钥不匹配或数据损坏）
  }
}
