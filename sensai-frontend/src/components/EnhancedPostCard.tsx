"use client";

import { useState } from 'react';
import { useAuth } from '@/lib/auth';
import { 
  ChevronUpIcon, 
  ChevronDownIcon, 
  ChatBubbleLeftIcon,
  LinkIcon,
  FlagIcon,
  CheckIcon,
  StarIcon,
  TagIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { 
  ChevronUpIcon as ChevronUpSolid,
  ChevronDownIcon as ChevronDownSolid,
  StarIcon as StarSolid,
  CheckIcon as CheckSolid
} from '@heroicons/react/24/solid';

interface PostCardProps {
  post: {
    id: number;
    hub_id: number;
    title?: string;
    content: string;
    post_type: string;
    created_at: string;
    author: string;
    votes: number;
    reply_count?: number;
    view_count?: number;
    author_reputation?: number;
    category?: string;
    tags?: string[];
    is_answered?: boolean;
    accepted_answer_id?: number;
    linked_tasks?: Array<{id: number; name: string; description: string}>;
    linked_skills?: Array<{name: string}>;
    linked_badges?: Array<{id: number; name: string; description: string}>;
    moderation_status?: string;
    ai_moderation_score?: number;
    is_pinned?: boolean;
    last_activity?: string;
    user_vote?: 'up' | 'down' | null;
    poll_options?: string[];
    poll_votes?: {[key: string]: number};
    poll_expires_at?: string;
    user_poll_votes?: string[];
    allow_multiple_answers?: boolean;
  };
  onVote?: (postId: number, voteType: 'up' | 'down' | null) => void;
  onReply?: (postId: number) => void;
  onReport?: (postId: number) => void;
  onMarkHelpful?: (postId: number) => void;
  onAcceptAnswer?: (postId: number, answerId: number) => void;
  isReply?: boolean;
  canModerate?: boolean;
}

export default function EnhancedPostCard({
  post,
  onVote,
  onReply,
  onReport,
  onMarkHelpful,
  onAcceptAnswer,
  isReply = false,
  canModerate = false
}: PostCardProps) {
  const { user } = useAuth();
  const [isExpanded, setIsExpanded] = useState(false);
  const [showReportDialog, setShowReportDialog] = useState(false);

  const getPostTypeIcon = () => {
    switch (post.post_type) {
      case 'question': return '❓';
      case 'poll': return '📊';
      case 'note': return '📝';
      case 'thread': return '💬';
      case 'reply': return '↳';
      default: return '💬';
    }
  };

  const getPostTypeColor = () => {
    switch (post.post_type) {
      case 'question': return post.is_answered ? 'text-green-500' : 'text-yellow-500';
      case 'poll': return 'text-blue-500';
      case 'note': return 'text-purple-500';
      case 'thread': return 'text-gray-400';
      case 'reply': return 'text-gray-500';
      default: return 'text-gray-400';
    }
  };

  const handleVote = (voteType: 'up' | 'down') => {
    if (!user || !onVote) return;
    const newVoteType = post.user_vote === voteType ? null : voteType;
    onVote(post.id, newVoteType);
  };

  const renderPollOptions = () => {
    if (post.post_type !== 'poll' || !post.poll_options) return null;

    const totalVotes = post.poll_votes ? Object.values(post.poll_votes).reduce((a, b) => a + b, 0) : 0;
    const isExpired = post.poll_expires_at ? new Date(post.poll_expires_at) < new Date() : false;
    const hasVoted = post.user_poll_votes && post.user_poll_votes.length > 0;

    return (
      <div className="mt-4 p-4 bg-[#0D0D0D] rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-gray-400">Poll Options</span>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>{totalVotes} votes</span>
            {post.poll_expires_at && (
              <span className={isExpired ? 'text-red-400' : ''}>
                <ClockIcon className="w-3 h-3 inline mr-1" />
                {isExpired ? 'Expired' : 'Active'}
              </span>
            )}
          </div>
        </div>
        
        <div className="space-y-2">
          {post.poll_options.map((option, index) => {
            const votes = post.poll_votes?.[option] || 0;
            const percentage = totalVotes > 0 ? (votes / totalVotes) * 100 : 0;
            const isUserChoice = post.user_poll_votes?.includes(option);
            
            return (
              <div key={index} className="relative">
                <button
                  className={`w-full text-left p-3 rounded border transition-colors ${
                    isUserChoice
                      ? 'border-purple-500 bg-purple-900/20'
                      : 'border-gray-700 hover:border-gray-600'
                  } ${isExpired || hasVoted ? 'cursor-default' : 'cursor-pointer'}`}
                  disabled={isExpired || hasVoted}
                  onClick={() => {
                    // Handle poll voting
                    if (!isExpired && !hasVoted && user) {
                      // Implement poll voting logic
                    }
                  }}
                >
                  <div className="flex justify-between items-center">
                    <span className="text-gray-200">{option}</span>
                    <span className="text-sm text-gray-400">{votes} ({percentage.toFixed(1)}%)</span>
                  </div>
                  {(hasVoted || isExpired) && (
                    <div className="absolute bottom-0 left-0 h-1 bg-purple-500 rounded-b transition-all"
                         style={{ width: `${percentage}%` }} />
                  )}
                </button>
              </div>
            );
          })}
        </div>
        
        {post.allow_multiple_answers && (
          <p className="text-xs text-gray-500 mt-2">Multiple answers allowed</p>
        )}
      </div>
    );
  };

  const renderTags = () => {
    if (!post.tags || post.tags.length === 0) return null;

    return (
      <div className="flex flex-wrap gap-1 mt-2">
        {post.tags.map((tag) => (
          <span
            key={tag}
            className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded flex items-center gap-1"
          >
            <TagIcon className="w-3 h-3" />
            {tag}
          </span>
        ))}
      </div>
    );
  };

  const renderLinkedContent = () => {
    const hasLinks = post.linked_tasks?.length || post.linked_skills?.length || post.linked_badges?.length;
    if (!hasLinks) return null;

    return (
      <div className="mt-3 p-3 bg-[#0D0D0D] rounded border border-gray-700">
        <div className="flex items-center gap-1 text-sm text-gray-400 mb-2">
          <LinkIcon className="w-4 h-4" />
          Related Content
        </div>
        
        <div className="space-y-2">
          {post.linked_tasks?.map((task) => (
            <div key={`task-${task.id}`} className="flex items-center gap-2 text-sm">
              <span className="text-blue-400">📋</span>
              <span className="text-gray-300">{task.name}</span>
            </div>
          ))}
          
          {post.linked_skills?.map((skill) => (
            <div key={`skill-${skill.name}`} className="flex items-center gap-2 text-sm">
              <span className="text-green-400">🎯</span>
              <span className="text-gray-300">{skill.name}</span>
            </div>
          ))}
          
          {post.linked_badges?.map((badge) => (
            <div key={`badge-${badge.id}`} className="flex items-center gap-2 text-sm">
              <span className="text-yellow-400">🏆</span>
              <span className="text-gray-300">{badge.name}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  return (
    <div className={`bg-[#1A1A1A] rounded-lg p-4 ${isReply ? 'ml-8 mt-2' : 'mb-4'} ${
      post.is_pinned ? 'border border-yellow-500/30' : ''
    }`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3">
          <div className={`text-lg ${getPostTypeColor()}`}>
            {getPostTypeIcon()}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              {post.title && (
                <h3 className="text-white font-medium">{post.title}</h3>
              )}
              {post.is_pinned && (
                <span className="text-yellow-500 text-xs">📌 Pinned</span>
              )}
              {post.category && (
                <span className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded">
                  {post.category}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <span>{post.author}</span>
              {post.author_reputation !== undefined && (
                <span className="flex items-center gap-1">
                  <StarIcon className="w-3 h-3" />
                  {post.author_reputation}
                </span>
              )}
              <span>•</span>
              <span>{formatTimeAgo(post.created_at)}</span>
              {post.view_count !== undefined && (
                <>
                  <span>•</span>
                  <span>{post.view_count} views</span>
                </>
              )}
            </div>
          </div>
        </div>
        
        {/* Moderation indicators */}
        <div className="flex items-center gap-2">
          {post.moderation_status === 'flagged' && canModerate && (
            <span className="text-yellow-500 text-xs">⚠️ Flagged</span>
          )}
          {post.ai_moderation_score !== undefined && post.ai_moderation_score > 0.5 && (
            <span className="text-orange-500 text-xs">🤖 AI Review</span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="text-gray-200 mb-3">
        <p className={isExpanded || post.content.length < 200 ? '' : 'line-clamp-3'}>
          {post.content}
        </p>
        {post.content.length > 200 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-purple-400 text-sm mt-1 hover:text-purple-300"
          >
            {isExpanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>

      {/* Poll options */}
      {renderPollOptions()}

      {/* Tags */}
      {renderTags()}

      {/* Linked content */}
      {renderLinkedContent()}

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-700">
        <div className="flex items-center gap-4">
          {/* Voting */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => handleVote('up')}
              className={`p-1 rounded transition-colors ${
                post.user_vote === 'up'
                  ? 'text-green-500'
                  : 'text-gray-400 hover:text-green-400'
              }`}
              disabled={!user}
            >
              {post.user_vote === 'up' ? (
                <ChevronUpSolid className="w-5 h-5" />
              ) : (
                <ChevronUpIcon className="w-5 h-5" />
              )}
            </button>
            <span className={`text-sm font-medium ${
              post.votes > 0 ? 'text-green-400' : 
              post.votes < 0 ? 'text-red-400' : 'text-gray-400'
            }`}>
              {post.votes}
            </span>
            <button
              onClick={() => handleVote('down')}
              className={`p-1 rounded transition-colors ${
                post.user_vote === 'down'
                  ? 'text-red-500'
                  : 'text-gray-400 hover:text-red-400'
              }`}
              disabled={!user}
            >
              {post.user_vote === 'down' ? (
                <ChevronDownSolid className="w-5 h-5" />
              ) : (
                <ChevronDownIcon className="w-5 h-5" />
              )}
            </button>
          </div>

          {/* Reply */}
          {onReply && (
            <button
              onClick={() => onReply(post.id)}
              className="flex items-center gap-1 text-gray-400 hover:text-white transition-colors text-sm"
            >
              <ChatBubbleLeftIcon className="w-4 h-4" />
              {post.reply_count || 0}
            </button>
          )}

          {/* Mark as helpful */}
          {onMarkHelpful && user && (
            <button
              onClick={() => onMarkHelpful(post.id)}
              className="flex items-center gap-1 text-gray-400 hover:text-yellow-400 transition-colors text-sm"
            >
              <StarIcon className="w-4 h-4" />
              Helpful
            </button>
          )}

          {/* Accept answer (for questions) */}
          {post.post_type === 'question' && onAcceptAnswer && user && !isReply && (
            <button
              onClick={() => onAcceptAnswer(post.id, post.id)}
              className={`flex items-center gap-1 transition-colors text-sm ${
                post.is_answered
                  ? 'text-green-500'
                  : 'text-gray-400 hover:text-green-400'
              }`}
            >
              {post.is_answered ? (
                <CheckSolid className="w-4 h-4" />
              ) : (
                <CheckIcon className="w-4 h-4" />
              )}
              {post.is_answered ? 'Answered' : 'Accept'}
            </button>
          )}
        </div>

        {/* Report */}
        {onReport && user && (
          <button
            onClick={() => setShowReportDialog(true)}
            className="text-gray-500 hover:text-red-400 transition-colors"
          >
            <FlagIcon className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Report Dialog - Simple version */}
      {showReportDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-[#1A1A1A] p-6 rounded-lg max-w-md w-full">
            <h3 className="text-white font-medium mb-4">Report Post</h3>
            <p className="text-gray-400 mb-4">Why are you reporting this post?</p>
            <div className="space-y-2 mb-4">
              {['spam', 'harassment', 'inappropriate', 'misinformation', 'other'].map((reason) => (
                <button
                  key={reason}
                  onClick={() => {
                    onReport?.(post.id);
                    setShowReportDialog(false);
                  }}
                  className="w-full text-left p-2 rounded hover:bg-gray-700 text-gray-300 capitalize"
                >
                  {reason}
                </button>
              ))}
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowReportDialog(false)}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
