"use client";

import { useState } from 'react';
import { Post } from '@/lib/api';
import { useAuth } from '@/lib/auth';

interface PollCardProps {
  post: Post;
  onVoteUpdate?: (postId: number) => void;
}

export default function PollCard({ post, onVoteUpdate }: PollCardProps) {
  const { user } = useAuth();
  const [selectedOptions, setSelectedOptions] = useState<number[]>(post.user_poll_votes || []);
  const [isVoting, setIsVoting] = useState(false);
  const [hasVoted, setHasVoted] = useState((post.user_poll_votes?.length || 0) > 0);

  const totalVotes = post.poll_options?.reduce((sum, option) => sum + option.vote_count, 0) || 0;
  const isPollExpired = post.poll_expires_at ? new Date(post.poll_expires_at) < new Date() : false;
  const canVote = !isPollExpired && !hasVoted && user;

  const handleOptionToggle = (optionId: number) => {
    if (isPollExpired || !user) return;

    if (post.allow_multiple_answers) {
      setSelectedOptions(prev => 
        prev.includes(optionId)
          ? prev.filter(id => id !== optionId)
          : [...prev, optionId]
      );
    } else {
      setSelectedOptions([optionId]);
    }
  };

  const handleSubmitVote = async () => {
    if (!user || selectedOptions.length === 0) return;

    setIsVoting(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/polls/${post.id}/vote`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: parseInt(user.id),
            option_ids: selectedOptions,
          }),
        }
      );

      if (response.ok) {
        setHasVoted(true);
        onVoteUpdate?.(post.id);
      }
    } catch (error) {
      console.error('Error voting on poll:', error);
    } finally {
      setIsVoting(false);
    }
  };

  const getPercentage = (voteCount: number) => {
    return totalVotes > 0 ? Math.round((voteCount / totalVotes) * 100) : 0;
  };

  return (
    <div className="bg-[#1A1A1A] rounded-lg p-6">
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">📊</span>
        <div>
          <h3 className="text-white font-medium">{post.title}</h3>
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <span>by {post.author}</span>
            <span>{new Date(post.created_at).toLocaleDateString()}</span>
            <span>{totalVotes} vote{totalVotes !== 1 ? 's' : ''}</span>
            {isPollExpired && <span className="text-red-400">Expired</span>}
          </div>
        </div>
      </div>

      <p className="text-gray-300 mb-6">{post.content}</p>

      <div className="space-y-3">
        {post.poll_options?.map((option) => {
          const percentage = getPercentage(option.vote_count);
          const isSelected = selectedOptions.includes(option.id);

          return (
            <div
              key={option.id}
              className={`relative rounded-lg border transition-colors ${
                canVote
                  ? `cursor-pointer ${
                      isSelected
                        ? 'border-purple-500 bg-purple-500/20'
                        : 'border-gray-700 hover:border-gray-600'
                    }`
                  : 'border-gray-700'
              }`}
              onClick={() => canVote && handleOptionToggle(option.id)}
            >
              <div className="relative p-4 z-10">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {canVote && (
                      <div
                        className={`w-4 h-4 rounded border-2 transition-colors ${
                          isSelected
                            ? 'bg-purple-500 border-purple-500'
                            : 'border-gray-500'
                        } ${
                          post.allow_multiple_answers ? 'rounded' : 'rounded-full'
                        }`}
                      >
                        {isSelected && (
                          <div className="w-full h-full flex items-center justify-center text-white text-xs">
                            ✓
                          </div>
                        )}
                      </div>
                    )}
                    <span className="text-white">{option.text}</span>
                  </div>
                  
                  {(hasVoted || isPollExpired) && (
                    <div className="text-right">
                      <div className="text-white font-medium">{percentage}%</div>
                      <div className="text-gray-400 text-sm">
                        {option.vote_count} vote{option.vote_count !== 1 ? 's' : ''}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Progress bar for voted/expired polls */}
              {(hasVoted || isPollExpired) && (
                <div
                  className="absolute inset-0 bg-purple-500/10 rounded-lg transition-all duration-500"
                  style={{ width: `${percentage}%` }}
                />
              )}
            </div>
          );
        })}
      </div>

      {canVote && selectedOptions.length > 0 && (
        <div className="mt-6 flex justify-between items-center">
          <div className="text-sm text-gray-400">
            {post.allow_multiple_answers && selectedOptions.length > 1
              ? `${selectedOptions.length} options selected`
              : '1 option selected'}
          </div>
          <button
            onClick={handleSubmitVote}
            disabled={isVoting}
            className="px-6 py-2 bg-purple-600 text-white rounded-full hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            {isVoting ? 'Voting...' : 'Submit Vote'}
          </button>
        </div>
      )}

      {post.poll_expires_at && !isPollExpired && (
        <div className="mt-4 text-sm text-gray-400">
          Expires: {new Date(post.poll_expires_at).toLocaleDateString()}
        </div>
      )}
    </div>
  );
}
