from scripts.check_secrets import scan_text


def test_secret_scanner_detects_tokens_and_private_keys() -> None:
    token = "github_" + "pat_" + "a" * 30
    private_key_header = "-----BEGIN " + "PRIVATE KEY-----"
    findings = scan_text(
        f"value={token}\n{private_key_header}\n"
    )

    assert len(findings) == 2


def test_secret_scanner_detects_non_placeholder_assignments() -> None:
    findings = scan_text(
        "UAMAS_API_TOKEN=real-secret-value\n"
        "UAMAS_ADMIN_TOKEN=changeme\n"
        "GITHUB_TOKEN=\n"
    )

    assert findings == ["non-placeholder secret assignment: UAMAS_API_TOKEN"]


def test_secret_scanner_allows_empty_examples() -> None:
    assert scan_text(
        "GITHUB_TOKEN=\n"
        "UAMAS_ADMIN_TOKEN=\n"
        "UAMAS_API_TOKEN=replace-me\n"
    ) == []
