import { FileText, Video, Headphones, FileImage } from 'lucide-react';

interface LearningNoteCardProps {
    type: 'pdf' | 'video' | 'audio' | 'image';
    title: string;
    description: string;
    tags: string[];
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

    return (
        <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden group cursor-pointer">
            {thumbnail ? (
                <div className="relative h-40 bg-gray-200">
                    <img src={thumbnail} alt={title} className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <Icon className="w-12 h-12 text-white" />
                    </div>
                </div>
            ) : (
                <div className="relative h-40 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                    <Icon className="w-16 h-16 text-gray-400" />
                </div>
            )}

            <div className="p-5">
                <div className={`inline-block px-3 py-1 rounded text-xs font-semibold mb-3 ${config.badgeColor}`}>
                    {config.badge}
                </div>

                <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                    {title}
                </h3>
                <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                    {description}
                </p>

                <div className="flex flex-wrap gap-2 mb-4">
                    {tags.map((tag, index) => (
                        <span
                            key={index}
                            className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded"
                        >
                            #{tag}
                        </span>
                    ))}
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">
                    {author && <span>{author}</span>}
                    <span>{timestamp}</span>
                </div>
            </div>
        </div>
    );
}
