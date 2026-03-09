"""Error translator for converting Pants errors to user-friendly messages."""

import logging

from src.intent.configuration import Configuration
from src.intent.data_models import IntentContext, TranslatedError, TranslationRule

logger = logging.getLogger("kiro.pants.intent")

# Default translation rules
DEFAULT_RULES = [
    TranslationRule(
        pattern=r"No targets? found",
        template="No tests found in {scope} {path}",
        priority=10,
    ),
    TranslationRule(
        pattern=r"Unknown target",
        template="Path contains no testable code: {path}",
        priority=10,
    ),
    TranslationRule(
        pattern=r"BUILD file not found",
        template="Directory not configured for Pants. Run 'pants tailor' to set up BUILD files",
        priority=10,
    ),
    TranslationRule(
        pattern=r"No such file or directory",
        template="Path does not exist: {path}",
        priority=10,
    ),
]


class ErrorTranslator:
    """Converts Pants error messages into intent-based, user-friendly language.

    Attributes:
        config: Configuration for error translation behavior
        translation_rules: List of translation rules to apply
    """

    def __init__(self, config: Configuration):
        """Initialize with configuration.

        Args:
            config: Configuration instance
        """
        self.config = config
        self._translation_rules: list[TranslationRule] = self._load_rules()

    def _load_rules(self) -> list[TranslationRule]:
        """Load translation rules (default + custom).

        Returns:
            List of translation rules
        """
        return DEFAULT_RULES + self.config.custom_translation_rules

    def translate_error(
        self,
        pants_error: str,
        intent_context: IntentContext,
    ) -> TranslatedError:
        """Translate Pants error to user-friendly message.

        Args:
            pants_error: Raw error message from Pants
            intent_context: Original intent parameters for context

        Returns:
            TranslatedError with user-friendly message and raw error
        """
        # Skip translation if disabled
        if not self.config.enable_error_translation:
            return TranslatedError(
                message=pants_error,
                raw_error=pants_error,
                rule_applied=None,
            )

        # Sort rules by priority (highest first)
        sorted_rules = sorted(self._translation_rules, key=lambda r: r.priority, reverse=True)

        # Try each rule
        for rule in sorted_rules:
            if rule.matches(pants_error):
                try:
                    user_message = rule.apply(pants_error, intent_context)
                    suggestion = self._extract_suggestion(rule, pants_error)
                    return TranslatedError(
                        message=user_message,
                        raw_error=pants_error,
                        rule_applied=rule.pattern,
                        suggestion=suggestion,
                    )
                except Exception as e:
                    logger.error("Error applying translation rule %s: %s", rule.pattern, e)
                    continue

        # No rule matched - return generic message
        return TranslatedError(
            message=f"Pants command failed. Error: {pants_error}",
            raw_error=pants_error,
            rule_applied=None,
        )

    def add_translation_rule(self, rule: TranslationRule) -> None:
        """Add custom translation rule.

        Args:
            rule: Translation rule to add
        """
        self._translation_rules.append(rule)
        # Re-sort by priority
        self._translation_rules.sort(key=lambda r: r.priority, reverse=True)

    def _extract_suggestion(self, rule: TranslationRule, error: str) -> str | None:
        """Extract actionable suggestion from error.

        Args:
            rule: The translation rule that matched
            error: The error message

        Returns:
            Optional suggestion string
        """
        if "BUILD file" in error or "tailor" in rule.template:
            return "pants tailor"
        return None
