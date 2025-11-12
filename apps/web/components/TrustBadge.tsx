/**
 * TrustBadge Component
 *
 * Displays data provenance and trust information for school listings.
 * Shows source type, confidence score, extraction timestamp, and provides
 * tooltip with detailed trust information.
 */

import { useState } from 'react';
import { Shield, Info, ExternalLink, Clock, CheckCircle, AlertTriangle } from 'lucide-react';
import { TrustBadgeProps } from '../lib/types';

export default function TrustBadge({
  sourceType,
  confidence,
  extractedAt,
  sourceUrl,
  extractorVersion,
  size = 'md',
  className = ''
}: TrustBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  // Determine confidence level and styling
  const getConfidenceInfo = (confidence: number) => {
    if (confidence >= 0.9) {
      return {
        level: 'High',
        color: 'text-green-600',
        bgColor: 'bg-green-100',
        icon: CheckCircle,
        description: 'Verified with high confidence'
      };
    } else if (confidence >= 0.7) {
      return {
        level: 'Medium',
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-100',
        icon: AlertTriangle,
        description: 'Reasonable confidence with some assumptions'
      };
    } else {
      return {
        level: 'Low',
        color: 'text-red-600',
        bgColor: 'bg-red-100',
        icon: AlertTriangle,
        description: 'Limited verification available'
      };
    }
  };

  const confidenceInfo = getConfidenceInfo(confidence);
  const ConfidenceIcon = confidenceInfo.icon;

  // Format extraction date
  const formatDate = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7);
      return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
    } else if (diffDays < 365) {
      const months = Math.floor(diffDays / 30);
      return `${months} month${months > 1 ? 's' : ''} ago`;
    } else {
      const years = Math.floor(diffDays / 365);
      return `${years} year${years > 1 ? 's' : ''} ago`;
    }
  };

  // Get source type display info
  const getSourceInfo = (sourceType: string) => {
    const sourceMap: Record<string, { label: string; icon: string; color: string }> = {
      'website': { label: 'Official Website', icon: '🌐', color: 'text-blue-600' },
      'directory': { label: 'Flight Directory', icon: '📚', color: 'text-purple-600' },
      'reddit': { label: 'Community Post', icon: '💬', color: 'text-orange-600' },
      'manual': { label: 'Manual Entry', icon: '✏️', color: 'text-gray-600' },
      'api': { label: 'API Source', icon: '🔌', color: 'text-green-600' },
      'default': { label: 'Verified Source', icon: '✅', color: 'text-gray-600' }
    };

    return sourceMap[sourceType.toLowerCase()] || sourceMap.default;
  };

  const sourceInfo = getSourceInfo(sourceType);

  // Size configurations
  const sizeConfig = {
    sm: {
      container: 'px-2 py-1 text-xs',
      icon: 'w-3 h-3',
      badge: 'w-4 h-4'
    },
    md: {
      container: 'px-3 py-1.5 text-sm',
      icon: 'w-4 h-4',
      badge: 'w-5 h-5'
    },
    lg: {
      container: 'px-4 py-2 text-base',
      icon: 'w-5 h-5',
      badge: 'w-6 h-6'
    }
  };

  const config = sizeConfig[size];

  return (
    <div className={`relative inline-block ${className}`}>
      {/* Main Badge */}
      <div
        className={`
          inline-flex items-center gap-2
          ${config.container}
          bg-white border border-gray-200 rounded-full
          shadow-sm hover:shadow-md transition-shadow cursor-help
          ${confidenceInfo.bgColor} ${confidenceInfo.color}
        `}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {/* Trust Shield Icon */}
        <Shield className={`${config.badge} ${confidenceInfo.color}`} />

        {/* Confidence Level */}
        <span className="font-medium">{confidenceInfo.level}</span>

        {/* Info Icon */}
        <Info className={`${config.icon} opacity-60`} />
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div className="
          absolute z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2
          w-80 p-4 bg-white border border-gray-200 rounded-lg shadow-lg
          text-sm text-gray-700
        ">
          {/* Tooltip Arrow */}
          <div className="
            absolute top-full left-1/2 transform -translate-x-1/2 -mt-1
            w-0 h-0 border-l-4 border-r-4 border-t-4
            border-transparent border-t-white
          "></div>

          {/* Content */}
          <div className="space-y-3">
            {/* Header */}
            <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
              <ConfidenceIcon className={`w-4 h-4 ${confidenceInfo.color}`} />
              <span className="font-semibold text-gray-900">
                Data Trust Score: {confidenceInfo.level}
              </span>
            </div>

            {/* Source Information */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">{sourceInfo.icon}</span>
                <span className="font-medium">{sourceInfo.label}</span>
              </div>

              <div className="flex items-center gap-2 text-gray-600">
                <Clock className="w-4 h-4" />
                <span>Updated {formatDate(extractedAt)}</span>
              </div>
            </div>

            {/* Confidence Details */}
            <div className="bg-gray-50 p-3 rounded-md">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-medium text-gray-700">Confidence Score</span>
                <span className={`text-xs font-bold ${confidenceInfo.color}`}>
                  {(confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full ${confidenceInfo.color.replace('text-', 'bg-')}`}
                  style={{ width: `${confidence * 100}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-600 mt-1">{confidenceInfo.description}</p>
            </div>

            {/* Additional Info */}
            <div className="text-xs text-gray-500 space-y-1">
              <div>Extractor: v{extractorVersion}</div>
              <div className="flex items-center gap-1">
                <span>Source:</span>
                <a
                  href={sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                >
                  View Original
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
