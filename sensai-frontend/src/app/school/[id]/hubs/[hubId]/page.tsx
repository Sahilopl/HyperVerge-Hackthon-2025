// adityavofficial-hyperverge-hackathon-2025/sensai-frontend/src/app/school/[id]/hubs/[hubId]/page.tsx

"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Plus, MessageSquare, ArrowLeft, ThumbsUp, MessageCircle, BarChart3, Search } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

// Define the types for Hub and Post
interface Hub {
    id: number;
    name: string;
    description: string;
}

interface Post {
    id: number;
    hub_id: number;
    title: string;
    content: string;
    post_type: string;
    created_at: string;
    author: string;
    votes: number;
    comment_count: number;
    // Enhanced fields
    moderation_status?: string;
    ai_moderation_score?: number;
    is_ai_moderated?: boolean;
    poll_options?: string[];
    poll_expires_at?: string;
    category?: string;
    is_pinned?: boolean;
    view_count?: number;
}

// CreatePostDialog Component
const CreatePostDialog = ({ open, onClose, hubId, schoolId, onPostCreated }: { open: boolean, onClose: () => void, hubId: string, schoolId: string, onPostCreated: (newPost: Post) => void }) => {
    const { user } = useAuth();
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [postType, setPostType] = useState('thread');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    // New poll functionality
    const [isPoll, setIsPoll] = useState(false);
    const [pollOptions, setPollOptions] = useState(['', '']);
    const [pollDuration, setPollDuration] = useState(7);

    const handleSubmit = async () => {
        if (!content.trim()) {
            setError('Content is required.');
            return;
        }
        if (postType !== 'reply' && !title.trim()) {
            setError('Title is required for new threads.');
            return;
        }
        if (isPoll && pollOptions.filter(option => option.trim()).length < 2) {
            setError('Poll must have at least 2 options.');
            return;
        }
        
        setIsLoading(true);
        try {
            const requestBody = {
                hub_id: parseInt(hubId),
                user_id: user?.id,
                title,
                content,
                post_type: isPoll ? 'poll' : postType,
                ...(isPoll && {
                    poll_options: pollOptions.filter(option => option.trim()),
                    poll_duration_days: pollDuration
                })
            };

            // Use the enhanced API endpoint with AI moderation
            const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/enhanced-hubs/posts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to create post.');
            }
            
            const newPostData = await response.json();
            
            // The enhanced API returns full post data, no need to refetch
            onPostCreated(newPostData);
            
            // Reset form
            setTitle('');
            setContent('');
            setPostType('thread');
            setIsPoll(false);
            setPollOptions(['', '']);
            setPollDuration(7);
            onClose();
        } catch (err) {
            console.error('Error creating post:', err);
            setError(err instanceof Error ? err.message : 'An error occurred. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    if (!open) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="w-full max-w-lg bg-[#1A1A1A] rounded-lg shadow-2xl" onClick={e => e.stopPropagation()}>
                <div className="p-6">
                    <h2 className="text-xl font-light text-white mb-4">Create a New Post</h2>
                    <div className="space-y-4">
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="Post Title"
                            className="w-full px-4 py-3 bg-[#0D0D0D] text-white rounded-lg font-light"
                        />
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            placeholder="What's on your mind?"
                            className="w-full h-32 px-4 py-3 bg-[#0D0D0D] text-white rounded-lg font-light"
                        />
                        
                        {/* Post Type Selector */}
                        <div className="flex gap-4">
                            <select
                                value={postType}
                                onChange={(e) => setPostType(e.target.value)}
                                className="px-4 py-2 bg-[#0D0D0D] text-white rounded-lg"
                            >
                                <option value="thread">Discussion Thread</option>
                                <option value="question">Question</option>
                                <option value="note">Note/Tutorial</option>
                            </select>
                            
                            <label className="flex items-center gap-2 text-white">
                                <input
                                    type="checkbox"
                                    checked={isPoll}
                                    onChange={(e) => setIsPoll(e.target.checked)}
                                    className="rounded"
                                />
                                Add Poll
                            </label>
                        </div>
                        
                        {/* Poll Options */}
                        {isPoll && (
                            <div className="space-y-3 p-4 bg-[#0D0D0D] rounded-lg">
                                <h3 className="text-white font-medium">Poll Options</h3>
                                {pollOptions.map((option, index) => (
                                    <div key={index} className="flex gap-2">
                                        <input
                                            type="text"
                                            value={option}
                                            onChange={(e) => {
                                                const newOptions = [...pollOptions];
                                                newOptions[index] = e.target.value;
                                                setPollOptions(newOptions);
                                            }}
                                            placeholder={`Option ${index + 1}`}
                                            className="flex-1 px-3 py-2 bg-[#1A1A1A] text-white rounded"
                                        />
                                        {index > 1 && (
                                            <button
                                                onClick={() => {
                                                    setPollOptions(pollOptions.filter((_, i) => i !== index));
                                                }}
                                                className="px-3 py-2 text-red-400 hover:text-red-300"
                                            >
                                                Remove
                                            </button>
                                        )}
                                    </div>
                                ))}
                                {pollOptions.length < 5 && (
                                    <button
                                        onClick={() => setPollOptions([...pollOptions, ''])}
                                        className="px-3 py-2 text-blue-400 hover:text-blue-300 text-sm"
                                    >
                                        + Add Option
                                    </button>
                                )}
                                <div className="flex items-center gap-2">
                                    <label className="text-white text-sm">Poll Duration:</label>
                                    <select
                                        value={pollDuration}
                                        onChange={(e) => setPollDuration(parseInt(e.target.value))}
                                        className="px-3 py-1 bg-[#1A1A1A] text-white rounded"
                                    >
                                        <option value={1}>1 day</option>
                                        <option value={3}>3 days</option>
                                        <option value={7}>1 week</option>
                                        <option value={14}>2 weeks</option>
                                        <option value={30}>1 month</option>
                                    </select>
                                </div>
                            </div>
                        )}
                        
                        {error && <p className="text-red-500 text-sm">{error}</p>}
                    </div>
                </div>
                <div className="flex justify-end gap-4 p-6">
                    <button onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-white" disabled={isLoading}>Cancel</button>
                    <button onClick={handleSubmit} className="px-6 py-2 bg-white text-black rounded-full" disabled={isLoading}>
                        {isLoading ? 'Posting...' : 'Post'}
                    </button>
                </div>
            </div>
        </div>
    );
};

// PostCard Component
const PostCard = ({ post, schoolId }: { post: Post, schoolId: string }) => {
    const isPoll = post.post_type === 'poll';
    const isQuestion = post.post_type === 'question';
    const isModerationFlagged = post.moderation_status === 'flagged' || post.moderation_status === 'hidden';
    
    return (
        <Link href={`/school/${schoolId}/posts/${post.id}`} className="block">
            <div className="bg-[#1A1A1A] p-6 rounded-lg transition-all hover:bg-[#222222] cursor-pointer">
                <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                        <h3 className="text-lg font-medium text-white">{post.title}</h3>
                        {post.is_pinned && (
                            <span className="px-2 py-1 text-xs bg-yellow-600 text-white rounded">📌 PINNED</span>
                        )}
                        {isPoll && (
                            <span className="px-2 py-1 text-xs bg-blue-600 text-white rounded">🗳️ POLL</span>
                        )}
                        {isQuestion && (
                            <span className="px-2 py-1 text-xs bg-green-600 text-white rounded">❓ Q&A</span>
                        )}
                        {post.is_ai_moderated && (
                            <span className="px-2 py-1 text-xs bg-purple-600 text-white rounded">🤖 AI Verified</span>
                        )}
                    </div>
                    {isModerationFlagged && (
                        <span className="px-2 py-1 text-xs bg-red-600 text-white rounded">⚠️ Flagged</span>
                    )}
                </div>
                
                <p className="text-gray-400 text-sm line-clamp-2 mb-4">{post.content}</p>
                
                {/* Show poll preview if it's a poll */}
                {isPoll && post.poll_options && post.poll_options.length > 0 && (
                    <div className="mb-4 p-3 bg-[#0D0D0D] rounded">
                        <div className="text-xs text-gray-400 mb-2">Poll Options:</div>
                        {post.poll_options.slice(0, 2).map((option, index) => (
                            <div key={index} className="text-sm text-gray-300">• {option}</div>
                        ))}
                        {post.poll_options.length > 2 && (
                            <div className="text-xs text-gray-500">+{post.poll_options.length - 2} more options</div>
                        )}
                        {post.poll_expires_at && (
                            <div className="text-xs text-gray-500 mt-1">
                                Expires: {new Date(post.poll_expires_at).toLocaleDateString()}
                            </div>
                        )}
                    </div>
                )}
                
                <div className="flex justify-between items-center text-xs text-gray-500">
                    <span>By {post.author}</span>
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1"><ThumbsUp size={14} /> {post.votes || 0}</span>
                        <span className="flex items-center gap-1"><MessageCircle size={14} /> {post.comment_count || 0}</span>
                        {post.view_count && <span>👁️ {post.view_count}</span>}
                        <span>{new Date(post.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
                
                {/* AI Moderation Score Display */}
                {post.ai_moderation_score !== undefined && post.ai_moderation_score > 0.3 && (
                    <div className="mt-2 text-xs text-gray-500">
                        AI Quality Score: {Math.round((1 - post.ai_moderation_score) * 100)}%
                    </div>
                )}
            </div>
        </Link>
    );
};

// Main Page Component
export default function HubPage() {
    const params = useParams();
    const schoolId = params.id as string;
    const hubId = params.hubId as string;
    const router = useRouter();

    const [hub, setHub] = useState<Hub | null>(null);
    const [posts, setPosts] = useState<Post[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
    // Enhanced features state
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState('all');

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Set default hub info immediately to avoid "Loading Hub..." display
                setHub({ id: parseInt(hubId), name: `Learning Hub ${hubId}`, description: 'Collaborative learning space' });
                
                // First try to get posts from enhanced API, fall back to basic API
                let postsData;
                try {
                    const postsResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/enhanced-hubs/hubs/${hubId}/posts`);
                    if (postsResponse.ok) {
                        postsData = await postsResponse.json();
                    } else {
                        throw new Error('Enhanced API posts fetch failed');
                    }
                } catch (enhancedError) {
                    console.log('Using basic API for posts');
                    const postsResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/${hubId}/posts`);
                    if (!postsResponse.ok) {
                        throw new Error(`Failed to fetch posts: ${postsResponse.status}`);
                    }
                    postsData = await postsResponse.json();
                }
                
                // Try to get specific hub info from organization hubs API
                try {
                    const hubResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/organization/${schoolId}`);
                    if (hubResponse.ok) {
                        const hubsData = await hubResponse.json();
                        const currentHub = hubsData.find((h: any) => h.id === parseInt(hubId));
                        if (currentHub) {
                            setHub(currentHub);
                        }
                    }
                } catch (hubError) {
                    console.log('Could not fetch specific hub info, keeping default');
                }
                
                setPosts(postsData);
            } catch (err) {
                console.error('Error fetching hub data:', err);
                setError('Could not load hub content. Please try again later.');
                // Set a fallback hub even on error
                setHub({ id: parseInt(hubId), name: `Learning Hub ${hubId}`, description: 'Learning Hub' });
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [hubId, schoolId]);
    
    const handlePostCreated = (newPost: Post) => {
        setPosts(prevPosts => [newPost, ...prevPosts]);
    };

    // Filter posts based on search and type
    const filteredPosts = posts.filter(post => {
        const matchesSearch = searchQuery === '' || 
            post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            post.content.toLowerCase().includes(searchQuery.toLowerCase());
        
        const matchesType = filterType === 'all' || 
            (filterType === 'polls' && post.post_type === 'poll') ||
            (filterType === 'questions' && post.post_type === 'question') ||
            (filterType === 'discussions' && post.post_type === 'thread') ||
            (filterType === 'pinned' && post.is_pinned);
        
        return matchesSearch && matchesType;
    });

    return (
        <>
            <Header />
            <div className="min-h-screen bg-black text-white">
                <main className="max-w-4xl mx-auto pt-6 px-8 pb-12">
                    <div className="mb-8">
                        <button onClick={() => router.back()} className="flex items-center text-gray-400 hover:text-white transition-colors mb-4">
                            <ArrowLeft size={16} className="mr-2" />
                            Back to Hubs
                        </button>
                        <div className="flex justify-between items-center">
                            <div>
                                <h1 className="text-3xl font-light">
                                    {hub ? hub.name : `Learning Hub ${hubId}`}
                                </h1>
                                <p className="text-gray-400 mt-1">
                                    {hub ? hub.description : 'Collaborative learning and discussion space'}
                                </p>
                            </div>
                            <button
                                onClick={() => setIsCreateDialogOpen(true)}
                                className="px-6 py-3 bg-white text-black text-sm font-medium rounded-full hover:opacity-90 transition-opacity flex items-center"
                            >
                                <Plus size={16} className="mr-2" />
                                Create Post
                            </button>
                        </div>
                        
                        {/* Enhanced Features Info */}
                        <div className="mt-4 flex gap-4 text-sm text-gray-400">
                            <span className="flex items-center gap-1">
                                🤖 AI Moderated
                            </span>
                            <span className="flex items-center gap-1">
                                🗳️ Polls Supported
                            </span>
                            <span className="flex items-center gap-1">
                                ❓ Q&A Format
                            </span>
                            <span className="flex items-center gap-1">
                                🏆 Reputation System
                            </span>
                        </div>
                    </div>

                    {/* Enhanced Search and Filter Bar */}
                    <div className="mb-6 flex gap-4 items-center">
                        <div className="relative flex-1 max-w-md">
                            <Search size={16} className="absolute left-3 top-3 text-gray-400" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search posts..."
                                className="w-full pl-10 pr-4 py-2 bg-[#1A1A1A] text-white rounded-lg border border-gray-700 focus:border-white focus:outline-none"
                            />
                        </div>
                        <select
                            value={filterType}
                            onChange={(e) => setFilterType(e.target.value)}
                            className="px-4 py-2 bg-[#1A1A1A] text-white rounded-lg border border-gray-700 focus:border-white focus:outline-none"
                        >
                            <option value="all">All Posts</option>
                            <option value="discussions">Discussions</option>
                            <option value="questions">Questions</option>
                            <option value="polls">Polls</option>
                            <option value="pinned">📌 Pinned</option>
                        </select>
                        
                        {posts.length > 0 && (
                            <div className="text-sm text-gray-400">
                                {filteredPosts.length} of {posts.length} posts
                            </div>
                        )}
                    </div>

                    {loading && (
                        <div className="flex justify-center items-center py-12">
                            <div className="w-12 h-12 border-t-2 border-b-2 border-white rounded-full animate-spin"></div>
                        </div>
                    )}

                    {error && <p className="text-center text-red-500">{error}</p>}

                    {!loading && !error && (
                        <div className="space-y-6">
                            {filteredPosts.length > 0 ? (
                                filteredPosts.map(post => (
                                    <PostCard key={post.id} post={post} schoolId={schoolId} />
                                ))
                            ) : posts.length > 0 ? (
                                <div className="text-center py-12">
                                    <h2 className="text-xl font-medium mb-2">No posts match your search</h2>
                                    <p className="text-gray-400">Try adjusting your search or filter settings.</p>
                                </div>
                            ) : (
                                <div className="text-center py-20">
                                    <h2 className="text-2xl font-medium mb-2">Be the First to Post</h2>
                                    <p className="text-gray-400 mb-6">This hub is empty. Start a conversation!</p>
                                    <p className="text-sm text-gray-500">✨ Your posts will be automatically moderated by AI for quality and safety</p>
                                </div>
                            )}
                        </div>
                    )}
                </main>
            </div>
            <CreatePostDialog
                open={isCreateDialogOpen}
                onClose={() => setIsCreateDialogOpen(false)}
                hubId={hubId}
                schoolId={schoolId}
                onPostCreated={handlePostCreated}
            />
        </>
    );
}