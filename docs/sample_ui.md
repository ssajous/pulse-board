```javascript
import React, { useState, useEffect, useMemo } from 'react';
import { 
  ThumbsUp, 
  ThumbsDown, 
  MessageSquarePlus, 
  Activity, 
  AlertCircle, 
  Trash2,
  TrendingUp,
  Clock
} from 'lucide-react';

/**
 * Mocks and Helpers
 */

// Generate a random ID (simulating UUID)
const generateId = () => crypto.randomUUID();

// Initial seed data to populate the board if empty
const SEED_DATA = [
  {
    id: '1',
    content: 'We should implement a 4-day work week for better work-life balance.',
    score: 12,
    created_at: new Date(Date.now() - 1000000).toISOString(),
  },
  {
    id: '2',
    content: 'The coffee machine in the break room needs an upgrade.',
    score: 5,
    created_at: new Date(Date.now() - 500000).toISOString(),
  },
  {
    id: '3',
    content: 'Let\'s organize a monthly hackathon event.',
    score: 8,
    created_at: new Date(Date.now() - 200000).toISOString(),
  },
  {
    id: '4',
    content: 'This is a controversial topic that might get downvoted.',
    score: -2,
    created_at: new Date(Date.now() - 50000).toISOString(),
  }
];

// Tailwind classes for consistent styling
const CARD_BASE = "bg-slate-800 border border-slate-700 rounded-xl shadow-lg shadow-slate-900/20 transition-all duration-200 hover:shadow-xl hover:shadow-slate-900/30";
const BTN_BASE = "flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-slate-900";

/**
 * Component: Toast Notification
 */
const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgClass = type === 'error' ? 'bg-rose-500' : 'bg-indigo-600';

  return (
    <div className={`fixed bottom-4 right-4 ${bgClass} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-slide-up z-50`}>
      {type === 'error' ? <Trash2 size={18} /> : <Activity size={18} />}
      <span className="text-sm font-medium">{message}</span>
    </div>
  );
};

/**
 * Component: Topic Form
 */
const TopicForm = ({ onSubmit }) => {
  const [content, setContent] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const charCount = content.length;
  const isOverLimit = charCount > 255;
  const isEmpty = charCount === 0 || content.trim().length === 0;
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isEmpty && !isOverLimit) {
      onSubmit(content);
      setContent('');
    }
  };

  return (
    <div className={`${CARD_BASE} p-6 mb-8 border-l-4 border-l-indigo-500`}>
      <h2 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
        <MessageSquarePlus className="text-indigo-400" size={20} />
        Submit a Topic
      </h2>
      <form onSubmit={handleSubmit} className="relative">
        <div className={`relative rounded-lg border transition-all duration-200 ${
            isFocused ? 'border-indigo-500 ring-2 ring-indigo-500/20' : 'border-slate-600'
          } ${isOverLimit ? 'border-rose-500 ring-rose-500/20' : ''}`}>
          
          <textarea
            className="w-full p-4 rounded-lg resize-none outline-none min-h-[100px] text-slate-200 placeholder:text-slate-500 bg-transparent"
            placeholder="What's on your mind? Share an idea with the community..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            maxLength={300} // Soft limit to allow typing past 255 for UX feedback
          />
          
          <div className="absolute bottom-3 right-3 flex items-center gap-3">
            <span className={`text-xs font-medium transition-colors ${
              isOverLimit ? 'text-rose-400' : 'text-slate-500'
            }`}>
              {charCount}/255
            </span>
          </div>
        </div>

        <div className="mt-3 flex justify-between items-center">
          <p className="text-xs text-slate-400">
            Topics starting at score 0. Removed if score reaches -5.
          </p>
          <button
            type="submit"
            disabled={isEmpty || isOverLimit}
            className={`${BTN_BASE} px-6 py-2 text-sm text-white
              ${isEmpty || isOverLimit 
                ? 'bg-slate-700 text-slate-500 cursor-not-allowed' 
                : 'bg-indigo-600 hover:bg-indigo-500 active:transform active:scale-95'
              }`}
          >
            Post Topic
          </button>
        </div>
      </form>
    </div>
  );
};

/**
 * Component: Topic Card
 */
const TopicCard = ({ topic, onVote }) => {
  const isNegative = topic.score < 0;
  const isDanger = topic.score <= -3; // Visual warning before deletion

  return (
    <div className={`${CARD_BASE} p-0 flex flex-col sm:flex-row overflow-hidden animate-fade-in`}>
      {/* Vote Section */}
      <div className={`
        flex sm:flex-col items-center justify-between sm:justify-center 
        p-4 sm:w-20 bg-slate-900/30 border-b sm:border-b-0 sm:border-r border-slate-700
        gap-3
      `}>
        <button
          onClick={() => onVote(topic.id, 'up')}
          className={`${BTN_BASE} w-10 h-10 hover:bg-emerald-500/10 text-slate-500 hover:text-emerald-400`}
          aria-label="Upvote"
        >
          <ThumbsUp size={20} />
        </button>

        <span className={`
          text-lg font-bold tabular-nums transition-colors duration-300
          ${topic.score > 0 ? 'text-emerald-400' : ''}
          ${topic.score === 0 ? 'text-slate-500' : ''}
          ${topic.score < 0 ? 'text-rose-400' : ''}
        `}>
          {topic.score}
        </span>

        <button
          onClick={() => onVote(topic.id, 'down')}
          className={`${BTN_BASE} w-10 h-10 hover:bg-rose-500/10 text-slate-500 hover:text-rose-400`}
          aria-label="Downvote"
        >
          <ThumbsDown size={20} />
        </button>
      </div>

      {/* Content Section */}
      <div className="flex-1 p-5 relative">
        <div className="flex items-start justify-between mb-2">
          <div className="text-xs text-slate-400 flex items-center gap-1">
            <Clock size={12} />
            {new Date(topic.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            <span className="mx-1">•</span>
             {new Date(topic.created_at).toLocaleDateString()}
          </div>
          {isDanger && (
            <div className="flex items-center gap-1 text-xs font-bold text-rose-300 bg-rose-500/20 px-2 py-1 rounded-full border border-rose-500/20">
              <AlertCircle size={12} />
              Risk of Removal
            </div>
          )}
        </div>
        
        <p className="text-slate-200 leading-relaxed text-lg break-words">
          {topic.content}
        </p>

        {/* Visual progress bar towards deletion for negative scores */}
        {isNegative && (
           <div className="mt-4 w-full h-1 bg-slate-700 rounded-full overflow-hidden">
             <div 
               className="h-full bg-rose-500 transition-all duration-500"
               style={{ width: `${Math.min(Math.abs(topic.score) * 20, 100)}%` }}
             />
           </div>
        )}
      </div>
    </div>
  );
};

/**
 * Main Application Component
 */
const App = () => {
  // Persistence Logic
  const [topics, setTopics] = useState(() => {
    const saved = localStorage.getItem('pulse_topics');
    return saved ? JSON.parse(saved) : SEED_DATA;
  });

  const [toast, setToast] = useState(null);

  // Persistence Effect
  useEffect(() => {
    localStorage.setItem('pulse_topics', JSON.stringify(topics));
  }, [topics]);

  // Sorting Logic (PRD 3.3)
  // Primary: Score Descending
  // Secondary: Created At Descending
  const sortedTopics = useMemo(() => {
    return [...topics].sort((a, b) => {
      if (b.score !== a.score) {
        return b.score - a.score;
      }
      return new Date(b.created_at) - new Date(a.created_at);
    });
  }, [topics]);

  // Topic Submission (PRD 2.1)
  const handleAddTopic = (content) => {
    const newTopic = {
      id: generateId(),
      content: content.trim(),
      score: 0,
      created_at: new Date().toISOString()
    };
    
    // Add to list
    setTopics(prev => [newTopic, ...prev]);
    
    // Show feedback
    setToast({ message: 'Topic published successfully', type: 'success' });
  };

  // Voting & Censure Logic (PRD 2.2 & 2.3)
  const handleVote = (id, direction) => {
    setTopics(prevTopics => {
      // Find the topic to check thresholds before updating
      const targetTopic = prevTopics.find(t => t.id === id);
      if (!targetTopic) return prevTopics;

      const delta = direction === 'up' ? 1 : -1;
      const newScore = targetTopic.score + delta;

      // Censure Rule: Score <= -5 (PRD 3.4)
      if (newScore <= -5) {
        // Trigger Toast for removal
        setToast({ 
          message: 'Topic removed by community censure (score reached -5)', 
          type: 'error' 
        });
        
        // Remove topic
        return prevTopics.filter(t => t.id !== id);
      }

      // Normal vote update
      return prevTopics.map(t => 
        t.id === id ? { ...t, score: newScore } : t
      );
    });
  };

  const clearStorage = () => {
    if(confirm("Reset all topics to default?")) {
      setTopics(SEED_DATA);
      localStorage.removeItem('pulse_topics');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 font-sans text-slate-100 pb-20">
      {/* Toast Container */}
      {toast && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast(null)} 
        />
      )}

      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-30">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg text-white">
              <Activity size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white leading-tight">Community Pulse</h1>
              <p className="text-xs text-slate-400 font-medium">Anonymous Feedback Board</p>
            </div>
          </div>
          <button 
            onClick={clearStorage}
            className="text-xs text-slate-500 hover:text-slate-300 underline"
          >
            Reset Demo
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        
        {/* Submit Section */}
        <TopicForm onSubmit={handleAddTopic} />

        {/* Sorting Indicator */}
        <div className="flex items-center gap-2 text-sm text-slate-400 mb-4 px-2">
          <TrendingUp size={16} />
          <span className="font-medium">Live Feed</span>
          <span className="w-1 h-1 rounded-full bg-slate-700 mx-1"></span>
          <span>Sorted by popularity</span>
        </div>

        {/* List Section */}
        <div className="space-y-4">
          {sortedTopics.length === 0 ? (
            <div className="text-center py-20 opacity-50">
              <MessageSquarePlus className="mx-auto h-12 w-12 text-slate-700 mb-3" />
              <p className="text-lg font-medium text-slate-500">No topics yet</p>
              <p className="text-sm text-slate-600">Be the first to start the conversation</p>
            </div>
          ) : (
            sortedTopics.map(topic => (
              <TopicCard 
                key={topic.id} 
                topic={topic} 
                onVote={handleVote} 
              />
            ))
          )}
        </div>
      </main>

      {/* CSS for simple animations */}
      <style>{`
        @keyframes slide-up {
          from { transform: translateY(100%); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        .animate-slide-up {
          animation: slide-up 0.3s ease-out forwards;
        }
        @keyframes fade-in {
          from { opacity: 0; transform: scale(0.98); }
          to { opacity: 1; transform: scale(1); }
        }
        .animate-fade-in {
          animation: fade-in 0.3s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default App;
```