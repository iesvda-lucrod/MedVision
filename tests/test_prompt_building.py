
try:
    from models.prompts import build_prompt, RadiologiaConfig
    payload = build_prompt(context=TEST_CTX, radio_config=TEST_CONFIG)
    assert "system" in payload and "prompt" in payload, "Faltan claves"
    assert len(payload["system"]) > 0, "system vacío"
    assert len(payload["prompt"]) > 0, "prompt vacío"
    print(f"   system ({len(payload['system'])} chars) ✓")
    print(f"   prompt ({len(payload['prompt'])} chars) ✓")
    print("\n✅ TEST 4 PASADO")
except Exception as e:
    print(f"\n❌ TEST 4 FALLIDO: {e}", file=sys.stderr)
