import os
import boto3
from dotenv import load_dotenv

load_dotenv()

# Test if converse method exists and works
def test_converse():
    try:
        # Set the bearer token
        api_key = os.getenv('BEDROCK_AGENTCORE_API_KEY')
        if not api_key:
            print("❌ BEDROCK_AGENTCORE_API_KEY not found in .env")
            return False

        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = api_key.strip()

        # Create client
        client = boto3.client("bedrock-runtime", region_name="us-east-1")

        # Check if converse method exists
        if not hasattr(client, 'converse'):
            print("❌ converse method not available in boto3 client")
            print(f"Boto3 version check needed")
            return False

        print("✓ converse method found in client")

        # Test the converse call
        response = client.converse(
            modelId="anthropic.claude-3-5-haiku-20241022-v1:0",
            messages=[{"role": "user", "content": [{"text": "Hello from test script"}]}]
        )

        if "output" in response and "message" in response["output"]:
            text = response["output"]["message"]["content"][0]["text"]
            print(f"✓ Converse successful! Response: {text[:100]}...")
            return True
        else:
            print(f"⚠️ Unexpected response format: {response}")
            return False

    except Exception as e:
        print(f"❌ Converse test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing converse method...")
    success = test_converse()
    if success:
        print("🎉 Converse method working correctly!")
    else:
        print("💥 Converse method has issues")
