"""
Implements a cursor playback strategy, enhancing the vanilla playback strategy by painting a red dot on the suggested target location and optionally self-correcting.

Send in a series of screenshots to GPT-4 and then ask GPT-4 to describe what happened. Then give it the sequence of actions (in concrete coordinates and keyboard inputs), as well as your proposed modification in natural language. Ask it to output the new action sequence. At each step, paint a red dot on the suggested target location, look at the screenshot with the dot, and optionally self-correct.

1. Given the recorded states, describe what happened.
2. Given the description of what happened, proposed modifications in natural language instructions, the current state, and the actions produced so far, produce the next action.

    -- Ahmadkhan02
"""

from pprint import pformat
from PIL import ImageDraw, Image
from loguru import logger

from openadapt import adapters, models, strategies, utils
from openadapt.strategies import vanilla


PROCESS_EVENTS = True
INCLUDE_WINDOW_DATA = False


class CursorReplayStrategy(vanilla.VanillaReplayStrategy):
    """Cursor replay strategy that paints a red dot on the suggested target location and optionally self-corrects."""

    def __init__(
        self,
        recording: models.Recording,
        replay_instructions: str = "",
        process_events: bool = PROCESS_EVENTS,
    ) -> None:
        """Initialize the CursorReplayStrategy.

        Args:
            recording (models.Recording): The recording object.
            replay_instructions (str): Natural language instructions
                for how recording should be replayed.
            process_events (bool): Flag indicating whether to process the events.
              Defaults to True.
        """
        super().__init__(recording, replay_instructions, process_events)

    def get_next_action_event(
        self,
        screenshot: models.Screenshot,
        window_event: models.WindowEvent,
    ) -> models.ActionEvent | None:
        """Get the next ActionEvent for replay.

        Args:
            screenshot (models.Screenshot): The screenshot object.
            window_event (models.WindowEvent): The window event object.

        Returns:
            models.ActionEvent or None: The next ActionEvent for replay or None
              if there are no more events.
        """
        if self.process_events:
            action_events = self.recording.processed_action_events
        else:
            action_events = self.recording.action_events

        self.action_event_idx += 1
        num_action_events = len(action_events)
        if self.action_event_idx >= num_action_events:
            raise StopIteration()
        logger.debug(f"{self.action_event_idx=} of {num_action_events=}")

        action_event = self.generate_action_event(
            screenshot,
            window_event,
            action_events,
            self.action_history,
            self.replay_instructions,
        )
        if not action_event:
            raise StopIteration()

        self.action_history.append(action_event)
        return action_event

    def generate_action_event(
        self,
        current_screenshot: models.Screenshot,
        current_window_event: models.WindowEvent,
        recorded_actions: list[models.ActionEvent],
        replayed_actions: list[models.ActionEvent],
        replay_instructions: str,
    ) -> models.ActionEvent:
        """Modify the given ActionEvents according to the given replay instructions.

        Given the description of what happened, proposed modifications in natural language
        instructions, the current state, and the actions produced so far, produce the next
        action.

        Args:
            current_screenshot (models.Screenshot): current state screenshot
            current_window_event (models.WindowEvent): current state window data
            recorded_actions (list[models.ActionEvent]): list of action events from the
                recording
            replayed_actions (list[models.ActionEvent]): list of actions produced during
                current replay
            replay_instructions (str): proposed modifications in natural language
                instructions

        Returns:
            (models.ActionEvent) the next action event to be played, produced by the model
        """
        current_image = current_screenshot.image
        current_window_dict = current_window_event.to_prompt_dict()
        recorded_action_dicts = [action.to_prompt_dict() for action in recorded_actions]
        replayed_action_dicts = [action.to_prompt_dict() for action in replayed_actions]

        # Paint a red dot on the suggested target location
        if replayed_actions:
            last_action = replayed_actions[-1]
            current_image = self.paint_red_dot(current_image, last_action.mouse_x, last_action.mouse_y)

        system_prompt = utils.render_template_from_file(
            "prompts/system.j2",
        )
        prompt = utils.render_template_from_file(
            "prompts/generate_action_event.j2",
            current_window=current_window_dict,
            recorded_actions=recorded_action_dicts,
            replayed_actions=replayed_action_dicts,
            replay_instructions=replay_instructions,
        )
        prompt_adapter = adapters.get_default_prompt_adapter()
        content = prompt_adapter.prompt(
            prompt,
            system_prompt,
            [current_image],
        )
        action_dict = utils.parse_code_snippet(content)
        logger.info(f"{action_dict=}")
        if not action_dict:
            # allow early stopping
            return None
        action = models.ActionEvent.from_dict(action_dict)
        logger.info(f"{action=}")
        return action

    def paint_red_dot(self, image: Image.Image, x: float, y: float) -> Image.Image:
        """Paint a red dot on the image at the specified coordinates.

        Args:
            image (Image.Image): The image to paint the red dot on.
            x (float): The x-coordinate of the red dot.
            y (float): The y-coordinate of the red dot.

        Returns:
            Image.Image: The modified image with the red dot.
        """
        draw = ImageDraw.Draw(image)
        radius = 5
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill="red")
        return image
