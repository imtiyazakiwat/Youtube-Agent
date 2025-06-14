from gradio_client import Client
import shutil
import os

def test_chatterbox():
    # Test text
    text = """Now let's make my mum's favourite. So three mars bars into the pan. 
    Then we add the tuna and just stir for a bit, just let the chocolate and fish infuse. 
    A sprinkle of olive oil and some tomato ketchup. Now smell that. Oh boy this is going to be incredible."""
    
    try:
        # Initialize client
        print("Initializing Chatterbox client...")
        client = Client("ResembleAI/chatterbox")
        
        # Generate audio
        print("Generating audio...")
        response = client.predict(
            text,
            None,
            0.5,
            0.8,
            0,
            0.5,
            api_name="/generate_tts_audio"
        )
        
        # Print full response details
        print("Full Response:")
        print(f"Type: {type(response)}")
        print(f"Content: {response}")
        if isinstance(response, tuple):
            print("\nTuple contents:")
            for i, item in enumerate(response):
                print(f"Item {i}: {type(item)} - {item}")
        
        # Save the file locally
        output_file = "output.wav"
        if os.path.exists(response):
            shutil.copy2(response, output_file)
            print(f"\nFile saved locally as: {output_file}")
        else:
            print("\nError: Temporary file not found")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    test_chatterbox()
