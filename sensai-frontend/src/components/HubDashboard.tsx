"use client";

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import EnhancedPostCard from '@/components/EnhancedPostCard';
import CreatePostDialog from '@/components/CreatePostDialog';
import { 
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
  BellIcon,
  UserPlusIcon,
  FireIcon,
  ClockIcon,
  ChartBarIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';
import { BellIcon as BellSolid } from '@heroicons/react/24/solid';

interface HubDashboardProps {
  hubId: string;
}

interface Post {
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
}

interface HubStats {
  id: number;
  post_count: number;
  subscriber_count: number;
  active_today: number;
  topics: string[];
  moderators: number[];
}

export default function HubDashboard({ hubId }: HubDashboardProps) {
  const { user } = useAuth();
  const [posts, setPosts] = useState<Post[]>([]);
  const [hubStats, setHubStats] = useState<HubStats | null>(null);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [showCreatePost, setShowCreatePost] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters and search
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPostType, setSelectedPostType] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<'relevance' | 'date' | 'votes' | 'replies'>('relevance');
  const [feedType, setFeedType] = useState<'all' | 'trending' | 'unanswered' | 'following'>('all');
  
  // Available filters
  const postTypes = ['thread', 'question', 'note', 'poll'];
  const categories = ['general', 'technical', 'academic', 'career', 'project'];
  const [availableTags, setAvailableTags] = useState<string[]>([]);

  useEffect(() => {
    if (hubId) {
      loadHubData();
      loadPosts();
      checkSubscriptionStatus();
    }
  }, [hubId, selectedPostType, selectedCategory, selectedTags, sortBy, feedType]);

  const loadHubData = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/${hubId}/stats`);
      if (response.ok) {
        const stats = await response.json();
        setHubStats(stats);
      }
    } catch (error) {
      console.error('Error loading hub data:', error);
    }
  };

  const loadPosts = async () => {
    try {
      setLoading(true);
      
      let url = `${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs`;
      let requestBody: any = {};

      if (feedType === 'trending') {
        url += `/${hubId}/trending`;
      } else if (searchQuery || selectedPostType !== 'all' || selectedCategory !== 'all' || selectedTags.length > 0) {
        // Use search endpoint for filtered results
        url += `/search`;
        requestBody = {
          query: searchQuery,
          hub_ids: [parseInt(hubId)],
          post_types: selectedPostType !== 'all' ? [selectedPostType] : undefined,
          category: selectedCategory !== 'all' ? selectedCategory : undefined,
          tags: selectedTags.length > 0 ? selectedTags : undefined,
          sort_by: sortBy,
          limit: 50,
          offset: 0
        };
      } else if (feedType === 'following' && user) {
        // Use personalized feed
        url += `/feed`;
        requestBody = {
          user_id: parseInt(user.id),
          feed_type: 'following',
          limit: 50,
          offset: 0
        };
      } else {
        // Default hub posts
        url += `/${hubId}/posts`;
      }

      const response = await fetch(url, {
        method: requestBody.query !== undefined || requestBody.user_id ? 'POST' : 'GET',
        headers: { 'Content-Type': 'application/json' },
        body: Object.keys(requestBody).length > 0 ? JSON.stringify(requestBody) : undefined
      });

      if (response.ok) {
        const postsData = await response.json();
        setPosts(Array.isArray(postsData) ? postsData : postsData.posts || []);
        
        // Extract available tags from posts
        const tags = new Set<string>();
        postsData.forEach((post: Post) => {
          post.tags?.forEach(tag => tags.add(tag));
        });
        setAvailableTags(Array.from(tags));
      }
    } catch (error) {
      console.error('Error loading posts:', error);
      setError('Failed to load posts');
    } finally {
      setLoading(false);
    }
  };

  const checkSubscriptionStatus = async () => {
    if (!user) return;
    
    try {
      // This would need to be implemented in the API
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/${hubId}/subscription/${user.id}`
      );
      if (response.ok) {
        const data = await response.json();
        setIsSubscribed(data.is_subscribed);
      }
    } catch (error) {
      console.error('Error checking subscription:', error);
    }
  };

  const handleSubscribe = async () => {
    if (!user) return;
    
    try {
      const url = `${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/${isSubscribed ? `${hubId}/subscribe/${user.id}` : 'subscribe'}`;
      const response = await fetch(url, {
        method: isSubscribed ? 'DELETE' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: isSubscribed ? undefined : JSON.stringify({
          user_id: parseInt(user.id),
          hub_id: parseInt(hubId)
        })
      });

      if (response.ok) {
        setIsSubscribed(!isSubscribed);
        if (hubStats) {
          setHubStats({
            ...hubStats,
            subscriber_count: hubStats.subscriber_count + (isSubscribed ? -1 : 1)
          });
        }
      }
    } catch (error) {
      console.error('Error toggling subscription:', error);
    }
  };

  const handleVote = async (postId: number, voteType: 'up' | 'down' | null) => {
    if (!user) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/posts/${postId}/vote`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: parseInt(user.id),
            vote_type: voteType,
            is_comment: false
          })
        }
      );

      if (response.ok) {
        setPosts(posts.map(post => {
          if (post.id === postId) {
            const oldVote = post.user_vote;
            let newVotes = post.votes;
            
            // Adjust vote count
            if (oldVote === 'up') newVotes -= 1;
            if (oldVote === 'down') newVotes += 1;
            if (voteType === 'up') newVotes += 1;
            if (voteType === 'down') newVotes -= 1;
            
            return { ...post, user_vote: voteType, votes: newVotes };
          }
          return post;
        }));
      }
    } catch (error) {
      console.error('Error voting:', error);
    }
  };

  const handleReport = async (postId: number) => {
    if (!user) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/posts/${postId}/report`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            post_id: postId,
            reporter_id: parseInt(user.id),
            reason: 'inappropriate',
            description: 'Reported via UI'
          })
        }
      );

      if (response.ok) {
        alert('Post reported successfully');
      }
    } catch (error) {
      console.error('Error reporting post:', error);
    }
  };

  const handleMarkHelpful = async (postId: number) => {
    if (!user) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/posts/${postId}/mark-helpful`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: parseInt(user.id) })
        }
      );

      if (response.ok) {
        // Optimistically update UI
        handleVote(postId, 'up');
      }
    } catch (error) {
      console.error('Error marking as helpful:', error);
    }
  };

  const handleAcceptAnswer = async (questionId: number, answerId: number) => {
    if (!user) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/posts/${questionId}/accept-answer`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            answer_id: answerId,
            user_id: parseInt(user.id)
          })
        }
      );

      if (response.ok) {
        setPosts(posts.map(post => {
          if (post.id === questionId) {
            return { ...post, is_answered: true, accepted_answer_id: answerId };
          }
          return post;
        }));
      }
    } catch (error) {
      console.error('Error accepting answer:', error);
    }
  };

  const handlePostCreated = (newPost: any) => {
    setPosts([newPost, ...posts]);
    setShowCreatePost(false);
    if (hubStats) {
      setHubStats({ ...hubStats, post_count: hubStats.post_count + 1 });
    }
  };

  const toggleTag = (tag: string) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Hub Header */}
      <div className="bg-[#1A1A1A] rounded-lg p-6 mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold text-white mb-2">Learning Hub</h1>
            {hubStats && (
              <div className="flex items-center gap-4 text-sm text-gray-400">
                <span>{hubStats.post_count} posts</span>
                <span>{hubStats.subscriber_count} subscribers</span>
                <span className="flex items-center gap-1">
                  <FireIcon className="w-4 h-4 text-orange-500" />
                  {hubStats.active_today} active today
                </span>
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={handleSubscribe}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                isSubscribed
                  ? 'bg-gray-600 text-white hover:bg-gray-700'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              }`}
              disabled={!user}
            >
              {isSubscribed ? (
                <BellSolid className="w-4 h-4" />
              ) : (
                <BellIcon className="w-4 h-4" />
              )}
              {isSubscribed ? 'Subscribed' : 'Subscribe'}
            </button>
            
            <button
              onClick={() => setShowCreatePost(true)}
              className="bg-white text-black px-4 py-2 rounded-lg hover:opacity-90 transition-opacity"
              disabled={!user}
            >
              Create Post
            </button>
          </div>
        </div>

        {/* Topics */}
        {hubStats?.topics && hubStats.topics.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {hubStats.topics.map(topic => (
              <span key={topic} className="px-2 py-1 bg-purple-900/30 text-purple-300 text-sm rounded">
                {topic}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Filters and Search */}
      <div className="bg-[#1A1A1A] rounded-lg p-4 mb-6">
        {/* Search */}
        <div className="relative mb-4">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search posts, topics, or content..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#0D0D0D] text-white rounded-lg placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        {/* Filter Row */}
        <div className="flex flex-wrap gap-4 items-center">
          {/* Feed Type */}
          <div className="flex items-center gap-2">
            <FunnelIcon className="w-4 h-4 text-gray-400" />
            <select
              value={feedType}
              onChange={(e) => setFeedType(e.target.value as any)}
              className="bg-[#0D0D0D] text-white rounded px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="all">All Posts</option>
              <option value="trending">Trending</option>
              <option value="unanswered">Unanswered</option>
              <option value="following">Following</option>
            </select>
          </div>

          {/* Post Type Filter */}
          <select
            value={selectedPostType}
            onChange={(e) => setSelectedPostType(e.target.value)}
            className="bg-[#0D0D0D] text-white rounded px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">All Types</option>
            {postTypes.map(type => (
              <option key={type} value={type} className="capitalize">{type}s</option>
            ))}
          </select>

          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-[#0D0D0D] text-white rounded px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category} className="capitalize">{category}</option>
            ))}
          </select>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="bg-[#0D0D0D] text-white rounded px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="relevance">Most Relevant</option>
            <option value="date">Most Recent</option>
            <option value="votes">Most Votes</option>
            <option value="replies">Most Replies</option>
          </select>
        </div>

        {/* Tags */}
        {availableTags.length > 0 && (
          <div className="mt-3">
            <div className="text-sm text-gray-400 mb-2">Tags:</div>
            <div className="flex flex-wrap gap-2">
              {availableTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    selectedTags.includes(tag)
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Posts */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto"></div>
            <p className="text-gray-400 mt-2">Loading posts...</p>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <p className="text-red-400">{error}</p>
            <button
              onClick={loadPosts}
              className="mt-2 px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-400">No posts found matching your criteria.</p>
            {user && (
              <button
                onClick={() => setShowCreatePost(true)}
                className="mt-2 px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
              >
                Create the first post
              </button>
            )}
          </div>
        ) : (
          posts.map((post) => (
            <EnhancedPostCard
              key={post.id}
              post={post}
              onVote={handleVote}
              onReport={handleReport}
              onMarkHelpful={handleMarkHelpful}
              onAcceptAnswer={handleAcceptAnswer}
              canModerate={user ? hubStats?.moderators?.includes(parseInt(user.id)) : false}
            />
          ))
        )}
      </div>

      {/* Create Post Dialog */}
      {showCreatePost && (
        <CreatePostDialog
          open={showCreatePost}
          onClose={() => setShowCreatePost(false)}
          hubId={hubId}
          onPostCreated={handlePostCreated}
        />
      )}
    </div>
  );
}
