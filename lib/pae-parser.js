'use strict';

const zlib = require('node:zlib');

const MAX_MEMBER_BYTES = 80 * 1024 * 1024;

function isGzip(buffer) {
  return buffer.length >= 2 && buffer[0] === 0x1f && buffer[1] === 0x8b;
}

function readTarString(buffer, start, length) {
  return buffer.subarray(start, start + length).toString('utf8').replace(/\0.*$/, '').trim();
}

function untar(buffer) {
  const files = [];
  let offset = 0;
  while (offset + 512 <= buffer.length) {
    const header = buffer.subarray(offset, offset + 512);
    if (header.every(b => b === 0)) break;
    const name = readTarString(header, 0, 100);
    const prefix = readTarString(header, 345, 155);
    const fullName = prefix ? `${prefix}/${name}` : name;
    const sizeText = readTarString(header, 124, 12).replace(/[^0-7]/g, '');
    const size = sizeText ? parseInt(sizeText, 8) : 0;
    const type = String.fromCharCode(header[156] || 0);
    const dataStart = offset + 512;
    const dataEnd = dataStart + size;
    if (dataEnd > buffer.length) throw new Error('Truncated tar archive.');
    if ((type === '\0' || type === '0' || type === '') && /\.(npz|npy)$/i.test(fullName) && size <= MAX_MEMBER_BYTES) {
      files.push({ name: fullName, buffer: Buffer.from(buffer.subarray(dataStart, dataEnd)) });
    }
    offset = dataStart + Math.ceil(size / 512) * 512;
  }
  return files;
}

function findEndOfCentralDirectory(buf) {
  const sig = 0x06054b50;
  const min = Math.max(0, buf.length - 0xffff - 22);
  for (let i = buf.length - 22; i >= min; i--) {
    if (buf.readUInt32LE(i) === sig) return i;
  }
  return -1;
}

function unzipNpz(buffer) {
  const eocd = findEndOfCentralDirectory(buffer);
  if (eocd < 0) throw new Error('Invalid NPZ/ZIP archive.');
  const entryCount = buffer.readUInt16LE(eocd + 10);
  const centralOffset = buffer.readUInt32LE(eocd + 16);
  const files = [];
  let pos = centralOffset;

  for (let i = 0; i < entryCount; i++) {
    if (pos + 46 > buffer.length || buffer.readUInt32LE(pos) !== 0x02014b50) throw new Error('Invalid ZIP central directory.');
    const method = buffer.readUInt16LE(pos + 10);
    const compressedSize = buffer.readUInt32LE(pos + 20);
    const uncompressedSize = buffer.readUInt32LE(pos + 24);
    const nameLen = buffer.readUInt16LE(pos + 28);
    const extraLen = buffer.readUInt16LE(pos + 30);
    const commentLen = buffer.readUInt16LE(pos + 32);
    const localOffset = buffer.readUInt32LE(pos + 42);
    const name = buffer.subarray(pos + 46, pos + 46 + nameLen).toString('utf8');

    if (/\.npy$/i.test(name) && uncompressedSize <= MAX_MEMBER_BYTES) {
      if (localOffset + 30 > buffer.length || buffer.readUInt32LE(localOffset) !== 0x04034b50) throw new Error('Invalid ZIP local header.');
      const localNameLen = buffer.readUInt16LE(localOffset + 26);
      const localExtraLen = buffer.readUInt16LE(localOffset + 28);
      const dataStart = localOffset + 30 + localNameLen + localExtraLen;
      const dataEnd = dataStart + compressedSize;
      if (dataEnd > buffer.length) throw new Error('Truncated ZIP member.');
      const compressed = buffer.subarray(dataStart, dataEnd);
      let output;
      if (method === 0) output = Buffer.from(compressed);
      else if (method === 8) output = zlib.inflateRawSync(compressed);
      else throw new Error(`Unsupported ZIP compression method ${method}.`);
      if (output.length !== uncompressedSize && uncompressedSize !== 0) throw new Error('ZIP member size mismatch.');
      files.push({ name, buffer: output });
    }
    pos += 46 + nameLen + extraLen + commentLen;
  }
  return files;
}

function halfToFloat(h) {
  const s = (h & 0x8000) ? -1 : 1;
  const e = (h >> 10) & 0x1f;
  const f = h & 0x03ff;
  if (e === 0) return s * Math.pow(2, -14) * (f / 1024);
  if (e === 31) return f ? NaN : s * Infinity;
  return s * Math.pow(2, e - 15) * (1 + f / 1024);
}

function parseNpy(input) {
  const u8 = input instanceof Uint8Array ? input : new Uint8Array(input);
  if (u8.length < 16 || u8[0] !== 0x93 || Buffer.from(u8.slice(1, 6)).toString('ascii') !== 'NUMPY') throw new Error('Invalid NPY file.');
  const major = u8[6];
  const view = new DataView(u8.buffer, u8.byteOffset, u8.byteLength);
  let headerLen, headerStart;
  if (major === 1) { headerLen = view.getUint16(8, true); headerStart = 10; }
  else { headerLen = view.getUint32(8, true); headerStart = 12; }
  const headerEnd = headerStart + headerLen;
  if (headerEnd > u8.length) throw new Error('Truncated NPY header.');
  const header = Buffer.from(u8.slice(headerStart, headerEnd)).toString('latin1');

  const descr = /['"]descr['"]\s*:\s*['"]([^'"]+)['"]/.exec(header)?.[1];
  const fortran = /['"]fortran_order['"]\s*:\s*True/.test(header);
  const shapeRaw = /['"]shape['"]\s*:\s*\(([^)]*)\)/.exec(header)?.[1];
  const shape = String(shapeRaw || '').split(',').map(x => Number(x.trim())).filter(Number.isFinite);
  if (!descr || shape.length !== 2 || shape.some(x => !Number.isInteger(x) || x <= 0)) throw new Error('Unsupported PAE NPY shape/header.');

  const [rows, cols] = shape;
  const count = rows * cols;
  const littleEndian = descr[0] !== '>';
  const kind = descr.replace(/^[<>=|]/, '');
  const bytesPer = ({ f2:2, f4:4, f8:8, i1:1, u1:1, i2:2, u2:2, i4:4, u4:4 })[kind];
  if (!bytesPer) throw new Error(`Unsupported NPY dtype ${descr}.`);
  if (headerEnd + count * bytesPer > u8.length) throw new Error('Truncated NPY data.');

  const dv = new DataView(u8.buffer, u8.byteOffset + headerEnd, count * bytesPer);
  const read = offset => {
    switch (kind) {
      case 'f2': return halfToFloat(dv.getUint16(offset, littleEndian));
      case 'f4': return dv.getFloat32(offset, littleEndian);
      case 'f8': return dv.getFloat64(offset, littleEndian);
      case 'i1': return dv.getInt8(offset);
      case 'u1': return dv.getUint8(offset);
      case 'i2': return dv.getInt16(offset, littleEndian);
      case 'u2': return dv.getUint16(offset, littleEndian);
      case 'i4': return dv.getInt32(offset, littleEndian);
      case 'u4': return dv.getUint32(offset, littleEndian);
    }
  };

  const raw = new Float64Array(count);
  for (let i = 0; i < count; i++) raw[i] = read(i * bytesPer);
  if (!fortran) return { rows, cols, values: raw };
  const values = new Float64Array(count);
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) values[r * cols + c] = raw[c * rows + r];
  return { rows, cols, values };
}

function isPaeName(name) {
  const n = String(name || '').toLowerCase();
  return /(^|[\/_\-.])(pae|predicted[_-]?aligned[_-]?error)(?=[\/_\-.]|$)/.test(n);
}

function sampleIndexFromName(name) {
  const m = /(?:^|[\/_\-.])sample[_-]?(\d+)(?=[\/_\-.]|$)/i.exec(String(name || ''));
  return m ? Number(m[1]) : null;
}

function priority(name) {
  const n = String(name).toLowerCase();
  if (/pae\.npy$/.test(n)) return 0;
  if (/predicted[_-]?aligned[_-]?error/.test(n)) return 1;
  if (/pae/.test(n)) return 2;
  return 10;
}

function candidateFromNpz(buffer, { outerName = '' } = {}) {
  const entries = unzipNpz(buffer).sort((a, b) => priority(a.name) - priority(b.name));
  const outerIsPae = isPaeName(outerName);
  let firstParseable = null;
  for (const entry of entries) {
    try {
      const parsed = parseNpy(entry.buffer);
      if (!firstParseable) firstParseable = { ...parsed, source: entry.name };
      if (isPaeName(entry.name)) return { ...parsed, source: entry.name };
    } catch { /* inspect next array */ }
  }
  // A PAE-labelled NPZ commonly stores its matrix as arr_0.npy. Only allow
  // that generic inner name when the outer archive member itself is explicitly PAE.
  return outerIsPae ? firstParseable : null;
}

function downsample(values, rows, cols, maxDim = 220) {
  if (rows <= maxDim && cols <= maxDim) return { rows, cols, values: Array.from(values, v => Number.isFinite(v) ? Number(v.toFixed(4)) : 0) };
  const scale = Math.max(rows / maxDim, cols / maxDim);
  const outRows = Math.max(1, Math.ceil(rows / scale));
  const outCols = Math.max(1, Math.ceil(cols / scale));
  const out = new Array(outRows * outCols);
  for (let orow = 0; orow < outRows; orow++) {
    const r0 = Math.floor(orow * rows / outRows), r1 = Math.max(r0 + 1, Math.floor((orow + 1) * rows / outRows));
    for (let ocol = 0; ocol < outCols; ocol++) {
      const c0 = Math.floor(ocol * cols / outCols), c1 = Math.max(c0 + 1, Math.floor((ocol + 1) * cols / outCols));
      let sum = 0, n = 0;
      for (let r = r0; r < r1; r++) for (let c = c0; c < c1; c++) {
        const v = Number(values[r * cols + c]); if (Number.isFinite(v)) { sum += v; n++; }
      }
      out[orow * outCols + ocol] = n ? Number((sum / n).toFixed(4)) : 0;
    }
  }
  return { rows: outRows, cols: outCols, values: out };
}

async function extractPaeFromArchive(archiveBuffer, { sampleIndex = null } = {}) {
  const tarBuffer = isGzip(archiveBuffer) ? zlib.gunzipSync(archiveBuffer) : archiveBuffer;
  let members = untar(tarBuffer).filter(m => isPaeName(m.name));

  if (sampleIndex !== null && sampleIndex !== undefined) {
    const wanted = Number(sampleIndex);
    if (!Number.isInteger(wanted) || wanted < 0) throw new Error('Invalid PAE sample index.');
    const exact = members.filter(m => sampleIndexFromName(m.name) === wanted);
    const generic = members.filter(m => sampleIndexFromName(m.name) === null);
    // For multi-sample output, never substitute a different sample's PAE.
    // Generic pae.npz is accepted as the single-sample convention only for sample 0.
    members = exact.length ? exact : (wanted === 0 ? generic : []);
  }

  members.sort((a, b) => priority(a.name) - priority(b.name));
  for (const member of members) {
    try {
      const parsed = /\.npz$/i.test(member.name)
        ? candidateFromNpz(member.buffer, { outerName: member.name })
        : { ...parseNpy(member.buffer), source: member.name };
      if (!parsed) continue;
      return { ...parsed, archive_member: member.name };
    } catch { /* keep looking only among explicitly PAE-labelled members */ }
  }
  return null;
}

module.exports = { candidateFromNpz, downsample, extractPaeFromArchive, isPaeName, parseNpy, sampleIndexFromName, unzipNpz, untar };
