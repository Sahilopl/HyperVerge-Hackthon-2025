"use client";

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { Post } from '@/lib/api'; // Make sure to export the Post type from your api lib
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

interface PollOption {
  id: string;
  text: string;
}

interface CreatePostDialogProps {
  open: boolean;
  onClose: () => void;
  hubId: string;
  onPostCreated: (newPost: Post) => void;
  parentPostId?: number; // Optional: for creating replies
}

export default function CreatePostDialog({
  open,
  onClose,
  hubId,
  onPostCreated,
  parentPostId,
}: CreatePostDialogProps) {
  const { user } = useAuth();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [postType, setPostType] = useState(parentPostId ? 'reply' : 'thread');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Poll-specific state
  const [pollOptions, setPollOptions] = useState<PollOption[]>([
    { id: '1', text: '' },
    { id: '2', text: '' }
  ]);
  const [pollDuration, setPollDuration] = useState(7); // days
  const [allowMultipleAnswers, setAllowMultipleAnswers] = useState(false);
  
  // QnA-specific state
  const [category, setCategory] = useState('general');
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');

  useEffect(() => {
    if (open) {
      // Reset form when dialog opens
      setTitle('');
      setContent('');
      setError('');
      setPostType(parentPostId ? 'reply' : 'thread');
      setPollOptions([{ id: '1', text: '' }, { id: '2', text: '' }]);
      setPollDuration(7);
      setAllowMultipleAnswers(false);
      setCategory('general');
      setTags([]);
      setNewTag('');
    }
  }, [open, parentPostId]);

  // Poll option management
  const addPollOption = () => {
    if (pollOptions.length < 6) {
      setPollOptions([...pollOptions, { id: Date.now().toString(), text: '' }]);
    }
  };

  const removePollOption = (id: string) => {
    if (pollOptions.length > 2) {
      setPollOptions(pollOptions.filter(option => option.id !== id));
    }
  };

  const updatePollOption = (id: string, text: string) => {
    setPollOptions(pollOptions.map(option => 
      option.id === id ? { ...option, text } : option
    ));
  };

  // Tag management
  const addTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim()) && tags.length < 5) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const handleSubmit = async () => {
    console.log('[CreatePost] handleSubmit start', { title, content, postType, parentPostId });
    
    // Validation
    if (!content.trim()) {
      console.log('[CreatePost] validation failed: empty content');
      setError('Content is required.');
      return;
    }
    
    if (postType !== 'reply' && !title.trim()) {
      console.log('[CreatePost] validation failed: empty title for thread');
      setError('Title is required for a new post.');
      return;
    }

    // Poll validation
    if (postType === 'poll') {
      const validOptions = pollOptions.filter(option => option.text.trim());
      if (validOptions.length < 2) {
        setError('Poll must have at least 2 options.');
        return;
      }
    }

    // QnA validation
    if (postType === 'question' && tags.length === 0) {
      setError('Questions should have at least one tag for better categorization.');
      return;
    }
    
    if (!user || !user.id) {
      console.log('[CreatePost] validation failed: no user');
      setError('You must be logged in to post.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Prepare post data based on type
      const basePostData = {
        hub_id: parseInt(hubId),
        user_id: parseInt(user.id),
        title: postType === 'reply' ? null : title,
        content,
        post_type: postType,
        parent_id: parentPostId,
      };

      // Add type-specific data
      let postData: any = { ...basePostData };
      
      if (postType === 'poll') {
        postData = {
          ...basePostData,
          poll_options: pollOptions.filter(option => option.text.trim()).map(option => option.text.trim()),
          poll_duration_days: pollDuration,
          allow_multiple_answers: allowMultipleAnswers,
        };
      } else if (postType === 'question') {
        postData = {
          ...basePostData,
          category,
          tags,
        };
      }

      console.log('[CreatePost] sending POST to /hubs/posts', postData);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/posts`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(postData),
        }
      );

      console.log('[CreatePost] POST response status', response.status);
      if (!response.ok) {
        const text = await response.text();
        console.error('[CreatePost] POST failed response text:', text);
        throw new Error('Failed to create post. Please try again.');
      }

      const newPostData = await response.json();
      console.log('[CreatePost] created post data', newPostData);

      // Refetch the full post
      console.log('[CreatePost] fetching full post details for id', newPostData.id);
      const postResponse = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/posts/${newPostData.id}`
      );
      console.log('[CreatePost] fetch full post status', postResponse.status);
      if (!postResponse.ok) {
        const text = await postResponse.text();
        console.error('[CreatePost] fetch full post failed text:', text);
        throw new Error('Failed to retrieve the created post.');
      }

      const newPost: Post = await postResponse.json();
      console.log('[CreatePost] full post object', newPost);

      onPostCreated(newPost);
      onClose();
    } catch (err) {
      console.error('[CreatePost] Error in handleSubmit', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred.');
    } finally {
      console.log('[CreatePost] handleSubmit end');
      setIsLoading(false);
    }
  };

  if (!open) return null;

  const postTypeOptions = [
    { value: 'thread', label: '💬 Thread', description: 'Start a discussion' },
    { value: 'question', label: '❓ Question', description: 'Ask for help or answers' },
    { value: 'note', label: '📝 Note', description: 'Share information or updates' },
    { value: 'poll', label: '📊 Poll', description: 'Create a poll for voting' },
  ];

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-[#1A1A1A] rounded-lg shadow-2xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          <h2 className="text-xl font-light text-white mb-4">
            {parentPostId ? 'Write a Reply' : 'Create a New Post'}
          </h2>
          
          <div className="space-y-4">
            {/* Post Type Selector */}
            {!parentPostId && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Post Type</label>
                <div className="grid grid-cols-2 gap-2">
                  {postTypeOptions.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setPostType(option.value)}
                      className={`p-3 text-left rounded-lg border transition-colors ${
                        postType === option.value
                          ? 'bg-purple-600 border-purple-500 text-white'
                          : 'bg-[#0D0D0D] border-gray-700 text-gray-300 hover:border-gray-600'
                      }`}
                    >
                      <div className="font-medium text-sm">{option.label}</div>
                      <div className="text-xs opacity-75">{option.description}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Title Field */}
            {!parentPostId && (
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={`Title of your ${postType}`}
                className="w-full px-4 py-3 bg-[#0D0D0D] text-white rounded-lg font-light placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            )}

            {/* Content Field */}
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder={
                postType === 'poll' ? 'Describe what you want to poll about...' :
                postType === 'question' ? 'Describe your question in detail...' :
                postType === 'note' ? 'Share your note or information...' :
                'Share your thoughts or start a discussion...'
              }
              className="w-full h-32 px-4 py-3 bg-[#0D0D0D] text-white rounded-lg font-light placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
            />

            {/* Poll Options */}
            {postType === 'poll' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-300">Poll Options</label>
                  <button
                    type="button"
                    onClick={addPollOption}
                    disabled={pollOptions.length >= 6}
                    className="text-purple-400 hover:text-purple-300 text-sm flex items-center gap-1 disabled:opacity-50"
                  >
                    <PlusIcon className="w-4 h-4" />
                    Add Option
                  </button>
                </div>
                
                {pollOptions.map((option, index) => (
                  <div key={option.id} className="flex gap-2">
                    <input
                      type="text"
                      value={option.text}
                      onChange={(e) => updatePollOption(option.id, e.target.value)}
                      placeholder={`Option ${index + 1}`}
                      className="flex-1 px-3 py-2 bg-[#0D0D0D] text-white rounded font-light placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                    />
                    {pollOptions.length > 2 && (
                      <button
                        type="button"
                        onClick={() => removePollOption(option.id)}
                        className="text-red-400 hover:text-red-300 p-2"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}

                <div className="grid grid-cols-2 gap-4 pt-2">
                  <div>
                    <label className="block text-sm text-gray-300 mb-1">Poll Duration (days)</label>
                    <input
                      type="number"
                      min="1"
                      max="30"
                      value={pollDuration}
                      onChange={(e) => setPollDuration(parseInt(e.target.value))}
                      className="w-full px-3 py-2 bg-[#0D0D0D] text-white rounded font-light focus:outline-none focus:ring-1 focus:ring-purple-500"
                    />
                  </div>
                  <div className="flex items-center">
                    <label className="flex items-center text-sm text-gray-300 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={allowMultipleAnswers}
                        onChange={(e) => setAllowMultipleAnswers(e.target.checked)}
                        className="mr-2 rounded"
                      />
                      Allow multiple answers
                    </label>
                  </div>
                </div>
              </div>
            )}

            {/* QnA Category and Tags */}
            {postType === 'question' && (
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2 bg-[#0D0D0D] text-white rounded font-light focus:outline-none focus:ring-1 focus:ring-purple-500"
                  >
                    <option value="general">General</option>
                    <option value="technical">Technical</option>
                    <option value="academic">Academic</option>
                    <option value="career">Career</option>
                    <option value="project">Project</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Tags</label>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="text"
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                      placeholder="Add a tag"
                      className="flex-1 px-3 py-2 bg-[#0D0D0D] text-white rounded font-light placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                    />
                    <button
                      type="button"
                      onClick={addTag}
                      disabled={tags.length >= 5}
                      className="px-3 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 text-sm"
                    >
                      Add
                    </button>
                  </div>
                  
                  {tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-1 bg-purple-100 text-purple-800 text-sm rounded flex items-center gap-1"
                        >
                          {tag}
                          <button
                            type="button"
                            onClick={() => removeTag(tag)}
                            className="text-purple-600 hover:text-purple-800"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
          </div>
        </div>
        
        <div className="flex justify-end gap-4 px-6 py-4 bg-[#111111] rounded-b-lg">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="px-6 py-2 bg-white text-black text-sm font-medium rounded-full hover:opacity-90 transition-opacity"
            disabled={isLoading}
          >
            {isLoading ? 'Publishing...' : `Publish ${postType}`}
          </button>
        </div>
      </div>
    </div>
  );
}
