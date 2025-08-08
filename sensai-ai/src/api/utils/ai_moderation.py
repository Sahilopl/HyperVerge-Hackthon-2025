"""
AI-based content moderation service for Learning Hubs & Forums.
Uses OpenAI's moderation API and custom logic for educational content filtering.
"""
# Load environment variables first
try:
    from api.load_env import *
except ImportError:
    pass

import openai
from openai import OpenAI
import asyncio
import re
import os
from typing import Dict, List, Any
from api.models import AIModerationResult
import logging

logger = logging.getLogger(__name__)

class AIContentModerator:
    def __init__(self, openai_api_key: str = None):
        # Use provided key or fallback to environment variable
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("No OpenAI API key provided. Set OPENAI_API_KEY environment variable.")
            raise ValueError("OpenAI API key is required for AI moderation")
        
        self.client = OpenAI(api_key=api_key)
        logger.info("AI Content Moderator initialized with OpenAI API key")
        
        # Educational platform specific toxic patterns
        self.toxic_patterns = [
            r'\b(?:stupid|dumb|idiot|moron)\s+(?:question|ask|asking)\b',
            r'\bjust\s+google\s+it\b',
            r'\b(?:rtfm|read\s+the\s+(?:fucking|f\*\*\*ing)\s+manual)\b',
            r'\b(?:noob|n00b|newbie)\s+(?:question|mistake|error)\b',
            r'\bwaste\s+of\s+time\b.*\b(?:question|post|discussion)\b',
        ]
        
        # Spam detection patterns
        self.spam_patterns = [
            r'(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/\S*)?.*(?:buy|sale|discount|offer|deal)',
            r'\b(?:click\s+here|visit\s+now|limited\s+time|act\s+fast)\b',
            r'\$\d+.*(?:per\s+hour|per\s+day|easy\s+money|work\s+from\s+home)',
        ]
        
        # Educational quality indicators (positive signals)
        self.quality_indicators = [
            r'\b(?:can\s+you\s+help|please\s+explain|could\s+someone|i\s+tried)\b',
            r'\b(?:here\s+is\s+my\s+code|my\s+approach|what\s+i\s+did)\b',
            r'\b(?:thank\s+you|thanks|appreciate|helpful|learned)\b',
            r'\b(?:example|solution|explanation|walkthrough|step\s+by\s+step)\b',
        ]

    async def moderate_content(self, content: str, title: str = "", context: Dict[str, Any] = None) -> AIModerationResult:
        """
        Perform comprehensive AI moderation on content.
        
        Args:
            content: The main content to moderate
            title: Optional title for context
            context: Additional context (author reputation, post type, etc.)
            
        Returns:
            AIModerationResult with moderation decision and explanation
        """
        try:
            full_text = f"{title} {content}".strip()
            
            # Initialize result
            result = AIModerationResult(
                is_toxic=False,
                toxicity_score=0.0,
                categories=[],
                suggested_action="approve",
                explanation="Content appears appropriate for educational discussion.",
                requires_human_review=False
            )
            
            # 1. OpenAI Moderation API
            try:
                moderation_response = await self._openai_moderation(full_text)
                if moderation_response.get("results", [{}])[0].get("flagged", False):
                    result.is_toxic = True
                    result.toxicity_score = max(result.toxicity_score, 0.8)
                    flagged_categories = moderation_response["results"][0]["categories"]
                    result.categories.extend([cat for cat, flagged in flagged_categories.items() if flagged])
                    result.suggested_action = "hide"
                    result.explanation = "Content flagged by OpenAI moderation for potentially harmful content."
            except Exception as e:
                logger.warning(f"OpenAI moderation failed: {e}")
            
            # 2. Educational platform specific checks
            educational_score = self._check_educational_toxicity(full_text)
            if educational_score > 0.6:
                result.is_toxic = True
                result.toxicity_score = max(result.toxicity_score, educational_score)
                result.categories.append("educational_hostility")
                result.suggested_action = "flag"
                result.explanation = "Content may be discouraging to learners or violates educational community standards."
            
            # 3. Spam detection
            spam_score = self._check_spam(full_text)
            if spam_score > 0.7:
                result.is_toxic = True
                result.toxicity_score = max(result.toxicity_score, spam_score)
                result.categories.append("spam")
                result.suggested_action = "delete"
                result.explanation = "Content appears to be spam or promotional material."
            
            # 4. Quality assessment for educational content
            quality_score = self._assess_educational_quality(full_text, context)
            if quality_score < 0.3 and len(content.split()) > 20:  # Only flag longer posts with very low quality
                result.categories.append("low_quality")
                if not result.is_toxic:  # Don't override more serious issues
                    result.suggested_action = "flag"
                    result.explanation = "Content may benefit from revision to be more helpful to the learning community."
                    result.requires_human_review = True
            
            # 5. Context-based adjustments
            if context:
                result = self._apply_context_adjustments(result, context)
            
            return result
            
        except Exception as e:
            logger.error(f"AI moderation failed: {e}")
            # Default to requiring human review on error
            return AIModerationResult(
                is_toxic=False,
                toxicity_score=0.0,
                categories=["moderation_error"],
                suggested_action="flag",
                explanation="Automatic moderation failed. Requires human review.",
                requires_human_review=True
            )

    async def _openai_moderation(self, text: str) -> Dict[str, Any]:
        """Call OpenAI moderation API."""
        response = await asyncio.to_thread(
            self.client.moderations.create,
            input=text
        )
        return response.model_dump()

    def _check_educational_toxicity(self, text: str) -> float:
        """Check for educational platform specific toxic patterns."""
        text_lower = text.lower()
        toxic_score = 0.0
        
        for pattern in self.toxic_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                toxic_score += 0.3 * len(matches)
        
        # Check for dismissive language
        dismissive_phrases = [
            "just google it", "this is basic", "everyone knows", "obviously you",
            "did you even try", "not hard to understand", "simple search"
        ]
        
        for phrase in dismissive_phrases:
            if phrase in text_lower:
                toxic_score += 0.2
        
        return min(toxic_score, 1.0)

    def _check_spam(self, text: str) -> float:
        """Detect spam patterns."""
        spam_score = 0.0
        
        for pattern in self.spam_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                spam_score += 0.4 * len(matches)
        
        # Check for excessive links
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        if len(urls) > 2:
            spam_score += 0.3
        
        # Check for repetitive content
        words = text.split()
        if len(words) > 10:
            unique_words = set(word.lower() for word in words)
            repetition_ratio = 1 - (len(unique_words) / len(words))
            if repetition_ratio > 0.7:
                spam_score += 0.3
        
        return min(spam_score, 1.0)

    def _assess_educational_quality(self, text: str, context: Dict[str, Any] = None) -> float:
        """Assess the educational quality of content."""
        quality_score = 0.5  # Start neutral
        
        text_lower = text.lower()
        
        # Positive indicators
        for pattern in self.quality_indicators:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            quality_score += 0.1 * len(matches)
        
        # Code blocks or technical examples boost quality
        if '```' in text or 'example:' in text_lower or 'for instance' in text_lower:
            quality_score += 0.2
        
        # Questions show engagement
        question_marks = text.count('?')
        quality_score += min(0.1 * question_marks, 0.3)
        
        # Effort indicators
        effort_phrases = ["i tried", "my approach", "here's what i did", "i researched"]
        for phrase in effort_phrases:
            if phrase in text_lower:
                quality_score += 0.15
        
        # Length and structure
        sentences = text.split('.')
        if len(sentences) > 2:  # Well-structured posts
            quality_score += 0.1
        
        # Context-based quality adjustments
        if context:
            post_type = context.get('post_type', '')
            if post_type == 'question' and len(text.split()) < 10:
                quality_score -= 0.2  # Very short questions
            elif post_type in ['note', 'thread'] and len(text.split()) > 50:
                quality_score += 0.1  # Substantial contributions
        
        return min(max(quality_score, 0.0), 1.0)

    def _apply_context_adjustments(self, result: AIModerationResult, context: Dict[str, Any]) -> AIModerationResult:
        """Apply context-based adjustments to moderation result."""
        # High reputation users get benefit of doubt
        author_reputation = context.get('author_reputation', 0)
        if author_reputation > 500:  # High reputation threshold
            result.toxicity_score *= 0.8  # Reduce toxicity score
            if result.suggested_action in ['flag', 'hide']:
                result.requires_human_review = True
                result.explanation += " (Flagged for review due to high author reputation)"
        
        # New users get stricter moderation
        elif author_reputation < 50:  # New user threshold
            if result.toxicity_score > 0.3:
                result.suggested_action = "flag"
                result.requires_human_review = True
        
        # Post type considerations
        post_type = context.get('post_type', '')
        if post_type == 'question' and 'low_quality' in result.categories:
            result.explanation += " Consider providing more context, code samples, or specific error messages."
        
        return result

# Global instance - will be initialized with environment variable
ai_moderator = None

def get_ai_moderator():
    """Get or create the global AI moderator instance."""
    global ai_moderator
    if ai_moderator is None:
        try:
            ai_moderator = AIContentModerator()
            logger.info("Global AI moderator instance created successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI moderator: {e}")
            raise
    return ai_moderator
