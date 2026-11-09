#!/usr/bin/env node
/**
 * 发布产物文件名统一脚本
 * （electron-builder afterAllArtifactBuild 钩子 + 独立 CLI 双模式）
 *
 * 背景：
 *   - NSIS 目标把安装包写成 "iMato Setup <version>.exe"（含空格）
 *   - latest.yml 中 electron-updater 使用的文件名是 "iMato-Setup-<version>.exe"
 *     （连字符，来自 electron-builder 的 safeArtifactName），并且增量更新按
 *     "<url>.blockmap" 查找 blockmap
 *   - 因此每次重建后必须把磁盘文件名改成与 latest.yml 一致，
 *     否则 1.0.4 的下载 404 / 自动更新失败会重现
 *
 * 用法：
 *   - 钩子：electron-builder.yml 中
 *       afterAllArtifactBuild: scripts/rename-artifacts.js
 *     （electron-builder 按工作目录解析该路径，故必须在 electron/ 目录执行打包）
 *   - CLI ：node scripts/rename-artifacts.js [release目录] [--all]
 *     打包完成后运行，做权威校验：sha512/size 不一致时退出码为 1
 *
 * 行为：
 *   1. 找到 "iMato Setup <ver>.exe" → 改名为 "iMato-Setup-<ver>.exe"
 *   2. 对应 ".exe.blockmap" 同步改名
 *   3. latest.yml 中的空格文件名改写为连字符（仅改名称，不动 sha512/size）
 *   4. 复算 sha512/size 并与 latest.yml 比对，输出改名前后的文件名与校验结果
 *
 * 时序说明：
 *   afterAllArtifactBuild 在 electron-builder 写出 latest.yml 之前执行，
 *   此时磁盘上的 latest.yml 可能还是上一次构建的旧文件。因此钩子模式对
 *   "旧 yml + 新 exe" 只标记 PENDING 并告警；CLI 模式是严格门禁。
 *
 * @module scripts/rename-artifacts
 */
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const TAG = '[rename-artifacts]';
const SPACE_EXE_RE = /^iMato Setup (.+)\.exe$/;
const TARGET_PREFIX = 'iMato-Setup-';
const LATEST_YML_NAME = 'latest.yml';
const HASH_CHUNK_BYTES = 4 * 1024 * 1024;

/** 默认发布目录：<repo>/release（本文件位于 <repo>/electron/scripts/） */
function defaultReleaseDir() {
  return path.resolve(__dirname, '..', '..', 'release');
}

function statSafe(targetPath) {
  try {
    return fs.statSync(targetPath);
  } catch {
    return null;
  }
}

/** 流式计算 SHA-512（Base64），避免把 190+ MiB 安装包读进内存 */
function sha512Base64(filePath) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('sha512');
    const stream = fs.createReadStream(filePath, { highWaterMark: HASH_CHUNK_BYTES });
    stream.on('data', (chunk) => hash.update(chunk));
    stream.on('error', reject);
    stream.on('end', () => resolve(hash.digest('base64')));
  });
}

/**
 * 收集待改名的产物
 * @param {string} dir 发布目录
 * @param {string[]|null} candidates 候选文件名（钩子模式来自 buildResult.artifactPaths）
 * @param {string|null} versionFilter 仅处理指定版本（CLI 模式默认取 latest.yml version）
 * @returns {Array<object>}
 */
function collectTargets(dir, candidates, versionFilter) {
  const names = candidates && candidates.length > 0 ? candidates : fs.readdirSync(dir);
  const targets = [];
  const seen = new Set();

  for (const rawName of names) {
    const name = path.basename(rawName);
    if (seen.has(name)) continue;
    seen.add(name);

    const matched = SPACE_EXE_RE.exec(name);
    if (!matched) continue;
    const version = matched[1];
    if (versionFilter && version !== versionFilter) continue;

    const targetName = `${TARGET_PREFIX}${version}.exe`;
    const blockmapSourceName = `${name}.blockmap`;
    const blockmapTargetName = `${targetName}.blockmap`;
    targets.push({
      version,
      sourceName: name,
      targetName,
      blockmapSourceName,
      blockmapTargetName,
      hasBlockmap: Boolean(statSafe(path.join(dir, blockmapSourceName))),
    });
  }
  return targets;
}

/** 执行单个文件改名（幂等：源不存在或目标已存在时跳过） */
function renameOne(dir, fromName, toName, log) {
  const fromPath = path.join(dir, fromName);
  const toPath = path.join(dir, toName);
  if (!statSafe(fromPath)) return null;
  if (statSafe(toPath)) {
    log(`WARN 目标已存在，跳过改名: "${toName}"（请人工确认是否残留旧包）`);
    return null;
  }
  fs.renameSync(fromPath, toPath);
  const after = statSafe(toPath);
  return { from: fromName, to: toName, size: after ? after.size : 0 };
}

/**
 * 解析 latest.yml 的关键字段
 * （只做轻量文本解析，不引入 YAML 依赖）
 */
function parseLatestYml(text) {
  const grab = (re) => {
    const matched = text.match(re);
    return matched ? matched[1].trim() : null;
  };
  const sha512Set = new Set([...text.matchAll(/sha512:\s*(\S+)/g)].map((m) => m[1]));
  const sizeRaw = grab(/^\s*size:\s*(\d+)\s*$/m);
  return {
    version: grab(/^version:\s*(.+)$/m),
    pathName: grab(/^path:\s*(.+)$/m),
    url: grab(/^\s*-\s*url:\s*(.+)$/m),
    sha512Set,
    size: sizeRaw ? Number(sizeRaw) : null,
  };
}

/**
 * 把 latest.yml 中出现的空格文件名改写为连字符（仅名称，sha512/size 不变）
 * @returns {number} 改写次数
 */
function rewriteLatestYml(ymlPath, renameMap, log) {
  const original = fs.readFileSync(ymlPath, 'utf-8');
  let text = original;
  let changed = 0;

  for (const [fromName, toName] of Object.entries(renameMap)) {
    const escaped = fromName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp(escaped, 'g');
    const hits = (text.match(re) || []).length;
    if (hits > 0) {
      text = text.replace(re, toName);
      changed += hits;
    }
  }

  if (changed > 0) {
    fs.writeFileSync(ymlPath, text, 'utf-8');
    log(`latest.yml: 已把 ${changed} 处空格文件名改写为连字符`);
  }
  return changed;
}

/**
 * 复算实际文件的 sha512/size，与 latest.yml 比对
 * @returns {Promise<object>} { status: 'match'|'mismatch'|'missing'|'missing-file'|'unparsable', ... }
 */
async function verifyLatestYml(dir) {
  const ymlPath = path.join(dir, LATEST_YML_NAME);
  const ymlStat = statSafe(ymlPath);
  if (!ymlStat) {
    return { status: 'missing', detail: 'latest.yml 不存在' };
  }

  const text = fs.readFileSync(ymlPath, 'utf-8');
  const info = parseLatestYml(text);
  if (!info.pathName) {
    return { status: 'unparsable', detail: 'latest.yml 缺少 path 字段', info };
  }

  const exePath = path.join(dir, info.pathName);
  const exeStat = statSafe(exePath);
  if (!exeStat) {
    return {
      status: 'missing-file',
      detail: `latest.yml 指向的文件不存在: "${info.pathName}"`,
      info,
    };
  }

  const hasSpace = /\s/.test(info.pathName);
  const actualSha = await sha512Base64(exePath);
  const ymlShas = [...info.sha512Set];
  const shaMatch = ymlShas.length > 0 && ymlShas.every((sha) => sha === actualSha);
  const sizeMatch = info.size === null || info.size === exeStat.size;
  // latest.yml 比 exe 旧 → 说明 electron-builder 尚未按本次构建重写 yml
  const stale = ymlStat.mtimeMs < exeStat.mtimeMs - 1000;

  const ok = !hasSpace && shaMatch && sizeMatch;
  return {
    status: ok ? 'match' : 'mismatch',
    ok,
    stale,
    hasSpace,
    exeName: info.pathName,
    size: exeStat.size,
    ymlSize: info.size,
    actualSha,
    ymlShas,
    shaMatch,
    sizeMatch,
    version: info.version,
  };
}

/** 打印改名前后的文件名与校验结果 */
function printReport(report, log) {
  log(`目录: ${report.dir}`);

  if (report.renamed.length === 0 && report.blockmaps.length === 0) {
    log('未发现需要改名的空格产物（可能已改名或尚未打包）');
  }
  for (const item of report.renamed) {
    log(`EXE     : "${item.from}" -> "${item.to}" (${item.size} B)`);
  }
  for (const item of report.blockmaps) {
    log(`BLOCKMAP: "${item.from}" -> "${item.to}" (${item.size} B)`);
  }

  if (report.ymlRewritten > 0) {
    // 已在 rewriteLatestYml 内打印明细
  } else if (report.ymlExists) {
    log('latest.yml: path/url 已是连字符格式（无需改写）');
  } else {
    log('latest.yml: 不存在（钩子阶段属正常，打包结束后由 electron-builder 生成）');
  }

  const v = report.verification || { status: 'missing' };
  if (v.status === 'match') {
    log(`sha512  : MATCH  文件="${v.exeName}" size=${v.size} B`);
    log(`sha512  : ${v.actualSha}`);
  } else if (v.status === 'mismatch') {
    const reasons = [];
    if (v.hasSpace) reasons.push('path/url 仍含空格');
    if (!v.shaMatch) reasons.push('sha512 不一致');
    if (!v.sizeMatch) reasons.push(`size 不一致(file=${v.size}, yml=${v.ymlSize})`);
    log(`sha512  : MISMATCH (${reasons.join('; ')})`);
    log(`  file sha512 = ${v.actualSha}`);
    log(`  yml  sha512 = ${v.ymlShas.join(' | ') || '(缺失)'}`);
  } else {
    log(`sha512  : 未校验 (${v.detail})`);
  }

  if (report.pending) {
    log('结论: PENDING —— latest.yml 尚未按本次构建重写，打包结束后请执行 npm run release:rename 复核');
  } else if (report.ok) {
    log('结论: OK —— 文件名与 latest.yml 一致，sha512 校验通过');
  } else {
    log('结论: FAIL —— 文件名或 sha512 与 latest.yml 不一致，禁止发布');
  }
}

/**
 * 主流程：改名 + 修正 latest.yml + 校验
 * @param {object} options
 * @param {string} [options.dir] 发布目录（默认 <repo>/release）
 * @param {string[]|null} [options.candidates] 候选文件名（钩子模式使用）
 * @param {boolean} [options.all] 忽略 latest.yml 版本过滤，处理全部空格产物
 * @param {boolean} [options.strict] 严格模式（校验失败视为不通过；CLI 使用）
 * @returns {Promise<object>} 执行报告
 */
async function renameArtifacts(options = {}) {
  const dir = path.resolve(options.dir || defaultReleaseDir());
  const strict = options.strict === true;
  const log = (...args) => console.log(TAG, ...args);

  if (!fs.existsSync(dir)) {
    throw new Error(`发布目录不存在: ${dir}`);
  }

  const ymlPath = path.join(dir, LATEST_YML_NAME);
  const ymlExists = Boolean(statSafe(ymlPath));
  const ymlVersion = ymlExists ? parseLatestYml(fs.readFileSync(ymlPath, 'utf-8')).version : null;
  const versionFilter = options.all === true ? null : ymlVersion;

  const report = {
    dir,
    renamed: [],
    blockmaps: [],
    ymlExists,
    ymlRewritten: 0,
    verification: null,
    pending: false,
    ok: true,
    strict,
  };

  const targets = collectTargets(dir, options.candidates, versionFilter);
  const renameMap = {};

  for (const target of targets) {
    const renamed = renameOne(dir, target.sourceName, target.targetName, log);
    if (renamed) {
      report.renamed.push(renamed);
      renameMap[renamed.from] = renamed.to;
    }
    if (target.hasBlockmap) {
      const renamedBlockmap = renameOne(dir, target.blockmapSourceName, target.blockmapTargetName, log);
      if (renamedBlockmap) report.blockmaps.push(renamedBlockmap);
    }
  }

  if (ymlExists && Object.keys(renameMap).length > 0) {
    report.ymlRewritten = rewriteLatestYml(ymlPath, renameMap, log);
  }

  report.verification = await verifyLatestYml(dir);
  const verification = report.verification;

  if (verification.status === 'match') {
    report.ok = true;
  } else if (strict) {
    report.ok = false;
  } else if (verification.stale) {
    report.pending = true;
    report.ok = true;
  } else {
    report.ok = false;
  }

  printReport(report, log);
  return report;
}

/**
 * electron-builder afterAllArtifactBuild 钩子
 * 说明：钩子必须在 latest.yml 写出之前完成改名，否则 yml 会引用旧文件名；
 *      这里的任何异常都不阻塞打包，权威校验交给 CLI 模式。
 * @param {object} buildResult electron-builder BuildResult
 * @returns {Promise<string[]>} 额外产物列表（本脚本不产生新产物，返回空数组）
 */
async function afterAllArtifactBuild(buildResult) {
  const dir = buildResult && buildResult.outDir ? buildResult.outDir : defaultReleaseDir();
  const candidates = buildResult && Array.isArray(buildResult.artifactPaths)
    ? buildResult.artifactPaths.map((artifactPath) => path.basename(artifactPath))
    : null;

  try {
    await renameArtifacts({ dir, candidates, strict: false });
  } catch (err) {
    console.error(`${TAG} [ERROR] 钩子执行失败（不阻塞打包）: ${err.message}`);
  }
  return [];
}

module.exports = afterAllArtifactBuild;
module.exports.afterAllArtifactBuild = afterAllArtifactBuild;
module.exports.renameArtifacts = renameArtifacts;
module.exports.sha512Base64 = sha512Base64;

/** CLI 入口 */
async function main() {
  const args = process.argv.slice(2);
  const dirArg = args.find((arg) => !arg.startsWith('--'));
  const dir = dirArg ? path.resolve(dirArg) : defaultReleaseDir();
  try {
    const report = await renameArtifacts({
      dir,
      all: args.includes('--all'),
      strict: true,
    });
    process.exitCode = report.ok ? 0 : 1;
  } catch (err) {
    console.error(`${TAG} [ERROR] ${err.message}`);
    process.exitCode = 1;
  }
}

if (require.main === module) {
  main();
}
