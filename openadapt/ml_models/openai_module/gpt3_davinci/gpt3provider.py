from base_provider import CompletionProvider, Modality, Capability, Availability


class GPT3CompletionProvider(CompletionProvider):
    Name = "GPT3-Davinci"
    Capabilities = [
        Capability.TRAINING,
        Capability.TUNING,
        Capability.USABLE_OUTPUT,
        Capability.INFERENCE,
    ]
    Modalities = [Modality.TEXT]
    Availabilities = [Availability.HOSTED]

    def finetune(self, prompt: str, completion: str):
        # TODO
        pass

    def infer(self, prompt: str):
        # TODO add call to local finetuned model for inference
        pass