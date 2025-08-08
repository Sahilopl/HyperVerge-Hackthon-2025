// adityavofficial-hyperverge-hackathon-2025/sensai-frontend/src/components/PostCard.tsx

import Link from "next/link";
import { ThumbsUp, MessageCircle, HelpCircle, FileText, StickyNote, BarChart3, CheckCircle } from "lucide-react";
import { Post } from '@/lib/api';
import PollCard from './PollCard';

interface PostCardProps {
    post: Post;
    schoolId: string;
    onPostUpdate?: (postId: number) => void;
}

export default function PostCard({ post, schoolId, onPostUpdate }: PostCardProps) {
    
    // If it's a poll, render the specialized PollCard
    if (post.post_type === 'poll') {
        return <PollCard post={post} onVoteUpdate={onPostUpdate} />;
    }
    
    const getPostIcon = () => {
        switch (post.post_type) {
            case 'question':
                return <HelpCircle size={16} className="text-blue-400" />;
            case 'note':
                return <StickyNote size={16} className="text-yellow-400" />;
            case 'poll':
                return <BarChart3 size={16} className="text-purple-400" />;
            case 'thread':
            default:
                return <FileText size={16} className="text-gray-400" />;
        }
    };

    const getPostTypeColor = () => {
        switch (post.post_type) {
            case 'question':
                return post.is_answered ? 'text-green-400 bg-green-400/10' : 'text-blue-400 bg-blue-400/10';
            case 'note':
                return 'text-yellow-400 bg-yellow-400/10';
            case 'poll':
                return 'text-purple-400 bg-purple-400/10';
            default:
                return 'text-gray-400 bg-gray-400/10';
        }
    };

    return (
        <Link href={`/school/${schoolId}/posts/${post.id}`} className="block">
            <div className="bg-[#1A1A1A] p-6 rounded-lg transition-all hover:bg-[#222222] cursor-pointer border border-transparent hover:border-gray-800">
                <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                        <h3 className="text-lg font-medium text-white mb-1">{post.title}</h3>
                        {/* Tags for questions */}
                        {post.post_type === 'question' && post.tags && post.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mb-2">
                                {post.tags.map((tag) => (
                                    <span
                                        key={tag}
                                        className="px-2 py-1 text-xs bg-gray-800 text-gray-300 rounded"
                                    >
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                    <div className={`flex items-center text-xs px-2 py-1 rounded-full ${getPostTypeColor()}`}>
                        {getPostIcon()}
                        <span className="ml-2 capitalize">{post.post_type}</span>
                        {post.post_type === 'question' && post.is_answered && (
                            <CheckCircle size={12} className="ml-1" />
                        )}
                    </div>
                </div>
                
                <p className="text-gray-400 text-sm line-clamp-2 mb-4">{post.content}</p>
                
                {/* Category for questions */}
                {post.post_type === 'question' && post.category && (
                    <div className="mb-3">
                        <span className="text-xs text-gray-500 bg-[#111111] px-2 py-1 rounded">
                            {post.category}
                        </span>
                    </div>
                )}
                
                <div className="flex justify-between items-center text-xs text-gray-500">
                    <span>By {post.author}</span>
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1">
                            <ThumbsUp size={14} /> {post.votes}
                        </span>
                        <span className="flex items-center gap-1">
                            <MessageCircle size={14} /> {post.comment_count}
                        </span>
                        <span>{new Date(post.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
            </div>
        </Link>
    );
}