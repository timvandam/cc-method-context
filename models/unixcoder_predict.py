from UniXcoder import UniXcoder
import torch

device = torch.device("cuda")
model = UniXcoder("microsoft/unixcoder-base")
model.to(device)


def generate(left_context: str) -> str:
    tokens_ids = model.tokenize([left_context], max_length=896, mode="<decoder-only>")
    source_ids = torch.tensor(tokens_ids).to(device)
    prediction_ids = model.generate(source_ids, decoder_only=True, beam_size=1, max_length=128)
    predictions = model.decode(prediction_ids)
    if len(predictions) == 0 or len(predictions[0]) == 0:
        return ''
    return predictions[0][0]


unixcoder = {
    "name": "UniXcoder",
    "generate": generate,
}
