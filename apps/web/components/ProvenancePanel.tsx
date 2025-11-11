/**
 * ProvenancePanel Component
 *
 * Displays data provenance information including source type,
 * confidence score, extraction details, and links to original sources.
 */

import { ExternalLink, Shield, Clock, Database, Code, Hash } from 'lucide-react';

interface ProvenancePanelProps {
  sourceType: string;
  sourceUrl: string;
  confidence: number;
  extractedAt: string;
  extractorVersion: string;
  snapshotId: string;
}

export default function ProvenancePanel({
  sourceType,
  sourceUrl,
  confidence,
  extractedAt,
  extractorVersion,
  snapshotId
}: ProvenancePanelProps) {
  // Parse extraction date
  const extractedDate = new Date(extractedAt);
  const now = new Date();
  const daysAgo = Math.floor((now.getTime() - extractedDate.getTime()) / (1000 * 60 * 60 * 24));

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSourceDisplayInfo = (sourceType: string) => {
    const sourceMap: Record<string, { label: string; icon: string; color: string; description: string }> = {
      'website': {
        label: 'Official Website',
        icon: '🌐',
        color: 'text-blue-600',
        description: 'Data extracted directly from the flight school\'s official website'
      },
      'directory': {
        label: 'Flight Directory',
        icon: '📚',
        color: 'text-purple-600',
        description: 'Information sourced from aviation industry directories and listings'
      },
      'reddit': {
        label: 'Community Discussion',
        icon: '💬',
        color: 'text-orange-600',
        description: 'Data collected from aviation community forums and discussions'
      },
      'manual': {
        label: 'Manual Entry',
        icon: '✏️',
        color: 'text-gray-600',
        description: 'Information manually verified and entered by our team'
      },
      'api': {
        label: 'Official API',
        icon: '🔌',
        color: 'text-green-600',
        description: 'Data retrieved from official aviation authority APIs'
      },
      'default': {
        label: 'Verified Source',
        icon: '✅',
        color: 'text-gray-600',
        description: 'Information from a verified aviation data source'
      }
    };

    return sourceMap[sourceType.toLowerCase()] || sourceMap.default;
  };

  const sourceInfo = getSourceDisplayInfo(sourceType);

  const getConfidenceLevel = (confidence: number) => {
    if (confidence >= 0.9) return { level: 'Very High', color: 'text-green-700', bgColor: 'bg-green-50' };
    if (confidence >= 0.8) return { level: 'High', color: 'text-green-600', bgColor: 'bg-green-50' };
    if (confidence >= 0.7) return { level: 'Good', color: 'text-yellow-600', bgColor: 'bg-yellow-50' };
    if (confidence >= 0.6) return { level: 'Moderate', color: 'text-orange-600', bgColor: 'bg-orange-50' };
    if (confidence >= 0.4) return { level: 'Low', color: 'text-red-600', bgColor: 'bg-red-50' };
    return { level: 'Very Low', color: 'text-red-700', bgColor: 'bg-red-50' };
  };

  const confidenceInfo = getConfidenceLevel(confidence);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center mb-4">
        <Shield className="w-5 h-5 mr-2 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">Data Provenance</h3>
      </div>

      <div className="space-y-4">
        {/* Source Type */}
        <div className="flex items-start space-x-3">
          <div className="text-2xl">{sourceInfo.icon}</div>
          <div className="flex-1">
            <div className={`font-medium ${sourceInfo.color}`}>{sourceInfo.label}</div>
            <div className="text-sm text-gray-600 mt-1">{sourceInfo.description}</div>
          </div>
        </div>

        {/* Confidence Score */}
        <div className={`${confidenceInfo.bgColor} rounded-lg p-4`}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center">
              <Database className="w-4 h-4 mr-2 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">Confidence Score</span>
            </div>
            <div className={`text-sm font-bold ${confidenceInfo.color}`}>
              {(confidence * 100).toFixed(0)}%
            </div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
            <div
              className={`h-2 rounded-full ${confidenceInfo.color.replace('text-', 'bg-')}`}
              style={{ width: `${confidence * 100}%` }}
            ></div>
          </div>
          <div className={`text-xs ${confidenceInfo.color}`}>
            {confidenceInfo.level} confidence
          </div>
        </div>

        {/* Extraction Details */}
        <div className="border-t border-gray-200 pt-4 space-y-3">
          <div className="flex items-center text-sm text-gray-600">
            <Clock className="w-4 h-4 mr-2" />
            <span>Extracted {formatDate(extractedDate)}</span>
            {daysAgo > 0 && (
              <span className="text-gray-500 ml-1">({daysAgo} days ago)</span>
            )}
          </div>

          <div className="flex items-center text-sm text-gray-600">
            <Code className="w-4 h-4 mr-2" />
            <span>Extractor v{extractorVersion}</span>
          </div>

          <div className="flex items-center text-sm text-gray-600">
            <Hash className="w-4 h-4 mr-2" />
            <span>Snapshot: {snapshotId}</span>
          </div>
        </div>

        {/* Source Link */}
        <div className="border-t border-gray-200 pt-4">
          <a
            href={sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 transition-colors"
          >
            <span>View Original Source</span>
            <ExternalLink className="w-4 h-4 ml-1" />
          </a>
        </div>

        {/* Data Freshness Indicator */}
        <div className="border-t border-gray-200 pt-4">
          <div className="text-xs text-gray-500">
            <div className="font-medium mb-1">Data Freshness</div>
            <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
              daysAgo <= 7 ? 'bg-green-100 text-green-800' :
              daysAgo <= 30 ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {daysAgo <= 7 ? 'Very Recent' :
               daysAgo <= 30 ? 'Recent' :
               daysAgo <= 90 ? 'Outdated' : 'Very Outdated'}
            </div>
          </div>
        </div>

        {/* Trust Statement */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
          <div className="flex items-start">
            <Shield className="w-4 h-4 mt-0.5 mr-2 text-blue-600 flex-shrink-0" />
            <div className="text-xs text-blue-800">
              <div className="font-medium mb-1">Transparency Guarantee</div>
              <div>
                All data includes source attribution, confidence scoring, and extraction timestamps
                to ensure transparency and enable verification of flight school information.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
