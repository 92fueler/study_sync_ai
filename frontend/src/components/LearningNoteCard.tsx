import { FileText, Video, Headphones, FileImage } from 'lucide-react';

interface Tag {
    type: 'format' | 'style' | 'topic';
    label: string;
}

interface LearningNoteCardProps {
    type: 'pdf' | 'video' | 'audio' | 'image';
    title: string;
    description: string;
    tags: Tag[]; // Updated to rich tags array
    author?: string;
    timestamp: string;
    thumbnail?: string;
}

const typeConfig = {
    pdf: {
        icon: FileText,
        badge: 'PDF Document',
        badgeColor: 'bg-red-100 text-red-600',
    },
    video: {
        icon: Video,
        badge: 'Video Lecture',
        badgeColor: 'bg-purple-100 text-purple-600',
    },
    audio: {
        icon: Headphones,
        badge: 'Audio Clip',
        badgeColor: 'bg-green-100 text-green-600',
    },
    image: {
        icon: FileImage,
        badge: 'Lecture Notes',
        badgeColor: 'bg-blue-100 text-blue-600',
    },
};

export default function LearningNoteCard({
    type,
    title,
    description,
    tags,
    author,
    timestamp,
    thumbnail,
}: LearningNoteCardProps) {
    const config = typeConfig[type];
    const Icon = config.icon;

    const formatTags = tags.filter(t => t.type === 'format');
    const otherTags = tags.filter(t => t.type !== 'format');

    // Helper to render varying tag styles
    const renderTag = (tag: Tag, index: number) => {
        if (tag.type === 'format') {
            return (
                <span key={index} className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
                    {tag.label}
                </span>
            );
        }
        if (tag.type === 'style') {
            return (
                <span key={index} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mr-1.5"></span>
                    {tag.label}
                </span>
            );
        }
        // default: topic
        return (
            <span key={index} className="text-xs text-gray-500 hover:text-gray-700 transition-colors">
                #{tag.label}
            </span>
        );
    };

    return (
        <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden group cursor-pointer h-full flex flex-col">
            {thumbnail ? (
                <div className="relative h-40 bg-gray-200 flex-shrink-0">
                    <img src={thumbnail} alt={title} className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <Icon className="w-12 h-12 text-white" />
                    </div>
                </div>
            ) : (
                <div className="relative h-40 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-16 h-16 text-gray-400" />
                </div>
            )}

            <div className="p-5 flex-1 flex flex-col">
                {/* Format Tags Section (Top) */}
                <div className="flex flex-wrap gap-2 mb-3">
                    {formatTags.length > 0 ? (
                        formatTags.map((tag, i) => renderTag(tag, i))
                    ) : (
                        // Fallback to type config if no explicit format tags
                        <div className={`inline-block px-3 py-1 rounded text-xs font-semibold ${config.badgeColor}`}>
                            {config.badge}
                        </div>
                    )}
                </div>

                <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                    {title}
                </h3>
                <p className="text-sm text-gray-600 mb-4 line-clamp-2 flex-1">
                    {description}
                </p>

                {/* Style & Topic Tags Section (Bottom) */}
                <div className="flex flex-wrap items-center gap-2 mb-4 pt-3 border-t border-gray-50">
                    {otherTags.map((tag, i) => renderTag(tag, i))}
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500 mt-auto">
                    {author && <span className="font-medium text-gray-700">{author}</span>}
                    <span>{timestamp}</span>
                </div>
            </div>
        </div>
    );
}
