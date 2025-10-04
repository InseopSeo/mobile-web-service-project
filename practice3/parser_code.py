# 멀티파트 추출 코드
import os
import sys
import re

def read_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def split_request(raw: bytes):
    """
    HTTP 요청을 [시작줄+헤더 블록] / [바디] 로 분리
    """
    sep = b"\r\n\r\n"
    alt = b"\n\n"
    idx = raw.find(sep)
    if idx == -1:
        idx = raw.find(alt)
        if idx == -1:
            raise ValueError("헤더와 바디를 구분할 수 없습니다.")
        headers = raw[:idx].decode("latin-1", errors="ignore")
        body = raw[idx + len(alt):]
    else:
        headers = raw[:idx].decode("latin-1", errors="ignore")
        body = raw[idx + len(sep):]
    return headers, body

def parse_headers_to_dict(headers_text: str):
    """
    여러 줄의 헤더 텍스트를 dict로 변환 (대소문자 무시)
    """
    headers = {}
    for line in headers_text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return headers

def get_boundary(content_type: str) -> bytes:
    """
    Content-Type 헤더에서 boundary= 값을 추출
    """
    # 예: multipart/form-data; boundary=----WebKitFormBoundaryabc123
    if not content_type:
        raise ValueError("Content-Type 헤더가 없습니다.")
    m = re.search(r'boundary=(?P<b>[^;]+)', content_type, re.IGNORECASE)
    if not m:
        raise ValueError("boundary 파라미터를 찾을 수 없습니다.")
    boundary = m.group("b").strip().strip('"')
    return boundary.encode("latin-1")

def sanitize_filename(name: str) -> str:
    """
    경로 이스케이프 및 위험 문자 제거
    """
    name = os.path.basename(name)
    # 윈도우/리눅스에서 문제될 수 있는 문자 제거
    return re.sub(r'[\\/:*?"<>|\r\n]+', "_", name)

def split_multipart_body(body: bytes, boundary: bytes):
    """
    multipart 바디를 파트 단위로 분리하여 각 파트의 (헤더바이트, 콘텐츠바이트)를 yield
    """
    dash_boundary = b"--" + boundary
    end_boundary = b"--" + boundary + b"--"

    # 바디가 반드시 \r\n으로 구분된다는 보장은 없으니 그대로 find/split 사용
    # 1) 양 끝의 \r\n 제거 시도 (있다면)
    if body.startswith(b"\r\n"):
        body = body[2:]
    # 2) 종료 경계 전까지의 덩어리를 얻기 위해 split
    segments = body.split(dash_boundary)
    parts = []
    for seg in segments:
        # 첫 세그먼트는 경계 이전의 프리앰블(대개 빈 내용)
        if not seg:
            continue
        # 경계 다음에는 \r\n이 하나 따라올 수 있음
        if seg.startswith(b"\r\n"):
            seg = seg[2:]
        # 종료 경계 처리
        if seg.startswith(b"--"):
            # end boundary: "--\r\n" 혹은 "--"로 끝
            break
        # 일반 파트: [헤더]\r\n\r\n[내용]\r\n
        header_sep = seg.find(b"\r\n\r\n")
        if header_sep == -1:
            header_sep = seg.find(b"\n\n")
            if header_sep == -1:
                # 비정형인 경우 스킵
                continue
            headers_blob = seg[:header_sep]
            content = seg[header_sep+2:]
        else:
            headers_blob = seg[:header_sep]
            content = seg[header_sep+4:]

        # 파트 끝의 \r\n 잘라내기 (대개 경계 앞에 \r\n 하나가 붙음)
        content = content.rstrip(b"\r\n")

        parts.append((headers_blob, content))
    return parts

def parse_part_headers(headers_blob: bytes):
    """
    파트 헤더 바이트 -> dict
    """
    text = headers_blob.decode("latin-1", errors="ignore")
    headers = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return headers

def parse_content_disposition(cd: str):
    """
    Content-Disposition: form-data; name="file"; filename="a.jpg"
    를 파싱해서 (name, filename) 반환. 없으면 None.
    """
    name = None
    filename = None
    if not cd:
        return name, filename
    # 파라미터 파싱
    # 큰따옴표/작은따옴표 모두 대응
    m_name = re.search(r'name=("|\')?([^"\';]+)\1?', cd, re.IGNORECASE)
    if m_name:
        name = m_name.group(2)
    m_fn = re.search(r'filename=("|\')?([^"\';]+)\1?', cd, re.IGNORECASE)
    if m_fn:
        filename = m_fn.group(2)
    return name, filename

def save_bytes(path: str, data: bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)

def main(bin_path: str, out_dir: str):
    raw = read_file_bytes(bin_path)
    headers_text, body = split_request(raw)
    req_headers = parse_headers_to_dict(headers_text)

    ct = req_headers.get("content-type", "")
    if "multipart/form-data" not in ct.lower():
        raise ValueError("이 요청은 multipart/form-data 가 아닙니다. Content-Type: " + ct)

    boundary = get_boundary(ct)
    parts = split_multipart_body(body, boundary)

    if not parts:
        raise ValueError("멀티파트 파트를 찾을 수 없습니다.")

    saved = []
    text_fields = []

    for i, (p_headers_blob, content) in enumerate(parts, start=1):
        p_headers = parse_part_headers(p_headers_blob)
        cd = p_headers.get("content-disposition", "")
        name, filename = parse_content_disposition(cd)

        if filename:  # 파일 파트
            safe_name = sanitize_filename(filename)
            if not safe_name:
                safe_name = f"part_{i}.bin"
            out_path = os.path.join(out_dir, safe_name)
            save_bytes(out_path, content)
            saved.append(out_path)
            print(f"[파일] name={name}, filename={filename} -> {out_path} ({len(content)} bytes)")
        else:
            # 일반 텍스트 필드 (이미지가 아닌 폼 값 등)
            # 확인용으로 저장 (원치 않으면 주석 처리)
            field_name = name or f"field_{i}"
            out_path = os.path.join(out_dir, f"{sanitize_filename(field_name)}.txt")
            # 파트에 별도 Content-Type이 있을 수 있음 (e.g., text/plain; charset=utf-8)
            ctype = p_headers.get("content-type", "")
            if "charset=" in ctype.lower():
                # charset 추출
                m = re.search(r'charset=([^\s;]+)', ctype, re.IGNORECASE)
                encoding = (m.group(1) if m else "utf-8").strip('"').strip("'")
            else:
                encoding = "utf-8"
            try:
                text = content.decode(encoding, errors="replace")
            except LookupError:
                text = content.decode("utf-8", errors="replace")
            os.makedirs(out_dir, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
            text_fields.append((field_name, out_path))
            print(f"[필드] name={field_name} -> {out_path} ({len(content)} bytes)")

    print("\n=== 추출 결과 ===")
    if saved:
        for p in saved:
            print("파일 저장:", p)
    else:
        print("저장된 파일이 없습니다 (파일 파트 미발견).")
    if text_fields:
        for name, p in text_fields:
            print(f"텍스트 필드[{name}] 저장: {p}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python extract_multipart.py <request_bin_path> <output_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
