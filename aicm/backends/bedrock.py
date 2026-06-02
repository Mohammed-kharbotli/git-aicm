import json

from aicm.utils import err, retry


def _stream_response(response, extract_text):
    message = []
    for event in response["body"]:
        chunk = json.loads(event["chunk"]["bytes"])
        text = extract_text(chunk)
        if text:
            print(text, end="", flush=True)
            message.append(text)
    print()
    return "".join(message)


def _import_boto3():
    try:
        import boto3
        return boto3
    except ImportError:
        err("boto3 not installed. Reinstall with: pipx install --force '.[bedrock]'")


def _get_client(config):
    boto3 = _import_boto3()
    try:
        session = boto3.Session(profile_name=config.get("profile"))
        return session.client("bedrock-runtime")
    except Exception as e:
        if "SSO" in str(e) or "expired" in str(e):
            profile = config.get("profile", "default")
            err(f"SSO session expired. Run: aws sso login --profile {profile}")
        err(f"AWS session error: {e}")


def generate(prompt, config):
    client = _get_client(config)

    model = config["model"]
    # Strip region prefix (eu., us., ap., me., af., etc.) before validation
    base_model = model.split(".", 1)[1] if "." in model and len(model.split(".", 1)[0]) <= 2 else model
    valid_prefixes = ["anthropic.", "meta.", "mistral.", "amazon.titan"]
    if not any(base_model.startswith(prefix) for prefix in valid_prefixes):
        err(f"Unknown model: {model}. Use anthropic.*, meta.*, mistral.*, or amazon.titan* models")

    is_anthropic = "anthropic" in model
    is_meta = "meta" in model
    is_mistral = "mistral" in model
    try:
        if is_anthropic:
            def _call_anthropic():
                response = client.invoke_model_with_response_stream(
                    modelId=model,
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 256,
                        "messages": [{"role": "user", "content": prompt}],
                    }),
                )
                return _stream_response(response, lambda c: c["delta"].get("text", "") if c.get("type") == "content_block_delta" else "")
            return retry(_call_anthropic, retries=2, delay=2.0)
        elif is_meta:
            def _call_meta():
                response = client.invoke_model_with_response_stream(
                    modelId=model,
                    body=json.dumps({"prompt": prompt, "max_gen_len": 256}),
                )
                return _stream_response(response, lambda c: c.get("generation", ""))
            return retry(_call_meta, retries=2, delay=2.0)
        elif is_mistral:
            def _call_mistral():
                response = client.invoke_model_with_response_stream(
                    modelId=model,
                    body=json.dumps({"prompt": prompt, "max_tokens": 256}),
                )
                return _stream_response(response, lambda c: c.get("outputs", [{}])[0].get("text", ""))
            return retry(_call_mistral, retries=2, delay=2.0)
        else:
            def _call_titan():
                response = client.invoke_model_with_response_stream(
                    modelId=model,
                    body=json.dumps({"inputText": prompt, "textGenerationConfig": {"maxTokenCount": 256}}),
                )
                return _stream_response(response, lambda c: c.get("outputText", c.get("completion", "")))
            return retry(_call_titan, retries=2, delay=2.0)
    except Exception as e:
        estr = str(e)
        if "AccessDenied" in estr:
            err("No permission for bedrock:InvokeModel. Ask your AWS admin to grant access.")
        if "UnauthorizedSSO" in estr or "expired" in estr:
            profile = config.get("profile", "default")
            err(f"SSO session expired. Run: aws sso login --profile {profile}")
        err(f"Bedrock error: {e}")


def setup(config):
    from aicm.utils import err
    try:
        profile = input("\nAWS profile (leave empty for default): ").strip() or None
    except EOFError:
        return config
    if profile:
        config["profile"] = profile
    boto3 = _import_boto3()
    try:
        session = boto3.Session(profile_name=config.get("profile"))
        session.client("sts").get_caller_identity()
        print("\nAWS credentials verified.")
    except Exception as e:
        err(f"AWS credentials issue: {e}")
    return config
