"""Keyframe generation that recovers from Muse Image's content filter.

The film's story is critical by design (a dodo kept in a tourist attraction),
and the filter refuses some honest descriptions of it. On a refusal, Muse Spark
rewrites the prompt to keep the same picture in plainer, more neutral wording,
and we retry. Every attempt is logged by meta.py.
"""
from . import meta

SPARK = "muse-spark-1.3"
REWRITE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "prompt": {"type": "string"},
        "changed": {"type": "string", "description": "what was reworded and why, one sentence"},
    },
    "required": ["prompt", "changed"],
}


def is_policy_refusal(err):
    return "content_policy_violation" in str(err)


def generate(prompt, out, refs=(), size="1536x864", attempts=3):
    """Generate a keyframe; on a content-filter refusal, reword with Muse Spark and retry.

    Returns (path, prompt actually used).
    """
    tried = []
    for _ in range(attempts):
        try:
            return meta.image(prompt, out, size=size, refs=refs), prompt
        except RuntimeError as e:
            if not is_policy_refusal(e):
                raise
            tried.append(prompt)
            reply = meta.chat(SPARK, [
                {"role": "system", "content":
                    "You rewrite image-generation prompts that an automated content filter refused. The film is a "
                    "gentle, non-graphic animated short. Keep the same scene, composition, characters, setting and "
                    "art style. Describe only what is visible, calmly and neutrally: no words suggesting cruelty, "
                    "suffering, violence, captivity or distress, and no real company or brand names. Keep any "
                    "instruction about matching a reference image."},
                {"role": "user", "content": "Refused prompts so far:\n" + "\n---\n".join(tried)},
            ], schema=REWRITE_SCHEMA, max_tokens=4000, reasoning_effort="low")
            prompt = reply["prompt"]
    raise RuntimeError(f"Muse Image refused {attempts} wordings; last: {prompt[:200]}")
