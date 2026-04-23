from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "选题报告.md"
TARGET = ROOT / "选题报告_Word版.rtf"


def rtf_escape(text: str) -> str:
    parts = []
    for ch in text:
        code = ord(ch)
        if ch == "\\":
            parts.append(r"\\")
        elif ch == "{":
            parts.append(r"\{")
        elif ch == "}":
            parts.append(r"\}")
        elif ch == "\t":
            parts.append(r"\tab ")
        elif ch == "\n":
            parts.append(r"\par " + "\n")
        elif 32 <= code <= 126:
            parts.append(ch)
        else:
            if code > 32767:
                code -= 65536
            parts.append(rf"\u{code}?")
    return "".join(parts)


def build_rtf(markdown: str) -> str:
    header = (
        r"{\rtf1\ansi\ansicpg936\deff0"
        r"{\fonttbl{\f0\fnil\fcharset134 SimSun;}{\f1\fnil\fcharset134 SimHei;}}"
        r"\viewkind4\uc1\pard\lang2052\f0\fs24 "
    )
    body = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            body.append(r"\par")
            continue
        if line.startswith("# "):
            text = line[2:].strip()
            body.append(rf"\pard\qc\b\f1\fs32 {rtf_escape(text)}\b0\f0\fs24\par")
            body.append(r"\par")
            continue
        if line.startswith("## "):
            text = line[3:].strip()
            body.append(rf"\pard\sb120\sa60\b\f1\fs28 {rtf_escape(text)}\b0\f0\fs24\par")
            continue
        if line.startswith("### "):
            text = line[4:].strip()
            body.append(rf"\pard\sb60\sa40\b\fs26 {rtf_escape(text)}\b0\fs24\par")
            continue
        body.append(rf"\pard\fi480\qj {rtf_escape(line)}\par")

    return header + "\n".join(body) + "}"


def main() -> None:
    markdown = SOURCE.read_text(encoding="utf-8")
    rtf = build_rtf(markdown)
    TARGET.write_text(rtf, encoding="ascii", errors="ignore")
    print(TARGET)


if __name__ == "__main__":
    main()
