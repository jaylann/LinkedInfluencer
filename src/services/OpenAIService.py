from __future__ import annotations

"""Services that interface with the OpenAI Python SDK (v≥1.80)."""


import json
import logging
from typing import Iterable, List, Sequence, cast

from openai import OpenAI
from openai._exceptions import OpenAIError
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.completion_create_params import ResponseFormat

from src.models.OpenAIConfig import OpenAIConfig
from src.models.Post import Post
from src.models.RSSItem import RSSItem
from src.utils.TextUtils import contains_markdown

logger = logging.getLogger("AppLogger")


class OpenAIService:  # pylint: disable=too-few-public-methods
    """High‑level wrapper around *chat.completions* for LinkedIn automation."""

    _MAX_TOKENS = 4096  # per‑request hard‑limit (model‑specific)

    def __init__(self, config: OpenAIConfig) -> None:  # noqa: D401
        """Create a dedicated :class:`OpenAI` client scoped to *config*."""
        logger.info("Initialising OpenAIService with model: %s", config.model)
        self._client: OpenAI = OpenAI(api_key=config.api_key)
        self._model: str = config.model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    JSON_MODE: ResponseFormat = cast(ResponseFormat, {"type": "json_object"})
    def generate_post(self, article: str, item: RSSItem) -> Post:
        """Generate a LinkedIn post that *must* be valid JSON (JSON mode)."""

        system_msg = _SYSTEM_PROMPT
        user_msg = f"<article>\n{article}\n</article>"

        # Build a statically‑typed *messages* list; cast is safe because the
        # dict literals satisfy the TypedDict contract.
        messages: List[ChatCompletionMessageParam] = cast(
            List[ChatCompletionMessageParam],
            [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
        )

        attempt = 0
        json_obj: dict | None = None
        while attempt < 5:
            attempt += 1
            try:
                completion = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=1.0,
                    max_tokens=self._MAX_TOKENS,
                    response_format=self.JSON_MODE,
                )
                json_obj = json.loads(completion.choices[0].message.content)

                # If the model smuggled markdown, strip and retry once.
                if contains_markdown(json_obj.get("content", "")) and attempt < 5:
                    messages[-1] = cast(
                        ChatCompletionMessageParam,
                        {"role": "user", "content": json_obj["content"]},
                    )
                    logger.debug("Markdown spotted – retrying (attempt %d)…", attempt + 1)
                    continue
                break  # success
            except (OpenAIError, json.JSONDecodeError) as exc:
                logger.exception("OpenAI call failed (%s) – attempt %d/5", exc, attempt)
                if attempt == 5:
                    raise

        if json_obj is None:
            raise RuntimeError("Unable to obtain valid JSON from OpenAI after 5 attempts.")

        post = Post(
            title=json_obj["title"],
            content=json_obj["content"],
            tags=json_obj["tags"],
            source_link=item.link,
            image_link="",
        )
        logger.info("Post generated ✓: %s", post.title)
        return post

    # ------------------------------------------------------------------
    # Headline picker
    # ------------------------------------------------------------------

    def choose_post(
            self,
            candidates: Sequence[RSSItem],
            already_posted: Sequence[Post],
    ) -> RSSItem:
        """Pick the most viral‑worthy headline that hasn't been posted yet."""

        system_msg = _HEADLINE_PICKER_PROMPT
        new_list = "\n".join(f"{i}. {it.title}" for i, it in enumerate(candidates))
        posted_list = "\n".join(f"{i}. {p.title}" for i, p in enumerate(already_posted))
        user_msg = f"<new_list>\n{new_list}\n</new_list>\n<posted_list>\n{posted_list}\n</posted_list>"

        messages: Iterable[ChatCompletionMessageParam] = cast(
            List[ChatCompletionMessageParam],
            [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
        )

        completion = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.7,
            max_tokens=50,
            response_format=self.JSON_MODE,
        )

        try:
            data = json.loads(completion.choices[0].message.content)
            chosen_idx = int(data["chosen_headline_index"])
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            logger.exception("Malformed assistant response: %s", exc)
            raise

        if not 0 <= chosen_idx < len(candidates):
            raise IndexError(
                f"Assistant chose invalid index {chosen_idx}; must be within 0‑{len(candidates)-1}."
            )

        chosen_item = candidates[chosen_idx]
        logger.info("Chosen headline ✓: %s", chosen_item.title)
        return chosen_item


_SYSTEM_PROMPT = """
<system>
  <role>
    You are a highly influential LinkedIn content creator with a strong software-engineering background.
  </role>

  <task>
    Given a full news article (supplied inside <article> tags by the user), write a LinkedIn post that maximises
    insight, engagement and virality among experienced software engineers.
  </task>

  <objectives>
    <objective id="1">Deliver non-obvious, technically valuable insight.</objective>
    <objective id="2">Trigger comments, reactions and shares.</objective>
    <objective id="3">Stay concise; no fluff.</objective>
  </objectives>

  <guidelines>
    <tone>Professional yet approachable. Hooks first, then analysis, then call-to-action.</tone>
    <seo>Weave in natural-language keywords that emerge from the article; avoid hash-symbols inside the body.</seo>
    <formatting>Plain text only. Use real newlines for paragraphs.</formatting>
  </guidelines>

  <output_format>
    <assistant_response_format>{"type":"json_object"}</assistant_response_format>
    <schema>
      <field name="title"   type="string"  desc="5-15 word hook" />
      <field name="content" type="string"  desc="Post body; plain text with \n breaks." />
      <field name="tags"    type="array"   desc="3-5 lower-case keywords, no #." />
    </schema>
    <!-- Example -->
    <example>
      {
        "title": "Why Small PRs Beat Big Releases",
        "content": "Ever merged a 5k-line PR? ...",
        "tags": ["devex","release","risk"]
      }
    </example>
  </output_format>

  <remember>
    Return *only* the JSON object, nothing else.
  </remember>
</system>
"""

_HEADLINE_PICKER_PROMPT = """
<system>
  <role>Expert viral-content strategist for LinkedIn.</role>

  <task>Select ONE headline from a candidate list that is most likely to go viral with professionals.</task>

  <selection_criteria>
    <relevance>Appeals to business, engineering or career-growth interests.</relevance>
    <emotional_hook>Evokes curiosity, surprise or urgency.</emotional_hook>
    <shareability>Readers feel compelled to pass it on.</shareability>
    <novelty>Topic is fresh, not over-saturated.</novelty>
  </selection_criteria>

  <input_format>
    The user will supply:
    <new_list>Numbered headlines, one per line.</new_list>
    <posted_list>Headlines already used.</posted_list>
  </input_format>

  <output_format>
    <assistant_response_format>{"type":"json_object"}</assistant_response_format>
    <schema>
      <field name="chosen_headline_index" type="string"
             desc="0-based index of the headline you picked from <new_list>."/>
    </schema>
    <example>{"chosen_headline_index":"2"}</example>
  </output_format>

  <rules>
    Return exactly one JSON object and NOTHING else.
  </rules>
</system>
"""