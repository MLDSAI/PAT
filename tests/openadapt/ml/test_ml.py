from openadapt.ml.base_provider import CompletionProviderFactory, Modality
from openadapt.ml.huggingface_models.generic_provider import GenericHuggingFaceProvider
from openadapt.ml.open_ai.gpt.gptprovider import GPTCompletionProvider

test_gpt_provider = GPTCompletionProvider()
test_hf_provider = GenericHuggingFaceProvider()


def test_openai_completion_provider():
    """
    Test to verify that the GPTCompletionProvider correctly fetches
    all available models within a user's organization, and can run inference
    on them. A prerequisite is having your OpenAI API key set up properly.
    """

    gpt_4_chat_response = test_gpt_provider.infer(
        "gpt-4", "What is your maximum context size?"
    )

    gpt_3_turbo_chat_response = test_gpt_provider.infer(
        "gpt-3.5-turbo", "What day is it today?"
    )

    davinci_completion_response = test_gpt_provider.infer("davinci", "Today is ")

    assert (
        len(gpt_3_turbo_chat_response) > 0
        and len(gpt_4_chat_response) > 0
        and len(davinci_completion_response) > 0
    )


def test_huggingface_completion_provider():
    """Test to verify that inference using HuggingFace Pipelines works."""
    inference_output = test_hf_provider.infer(
        "What is the next number in the series 1, 3, 5, 7 ",
        "gpt2-medium",
        "text-generation",
        trust_remote_code=True,
    )

    assert len(inference_output) > 0


def test_abstract_completion_provider_factory():
    """Test that the provider factory class gets completion providers with Modality.TEXT."""
    test_modality = Modality.TEXT
    providers_list = CompletionProviderFactory.get_for_modality(test_modality)

    assert providers_list
    for completion_providers in providers_list:
        assert test_modality in completion_providers.Modalities