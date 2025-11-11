/**
 * Side Panel Component
 * Container for tabs (Moves and Chat)
 */

import { useState } from 'react';
import { MovesTab } from './MovesTab';
import { ChatTab } from './ChatTab';

interface SidePanelProps {
  moves: string[];
}

type Tab = 'moves' | 'chat';

export function SidePanel({ moves }: SidePanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>('chat');

  return (
    <div className="h-full flex flex-col bg-white shadow-lg">
      {/* Tab Header */}
      <div className="flex border-b bg-gray-50">
        <button
          onClick={() => setActiveTab('moves')}
          className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
            activeTab === 'moves'
              ? 'text-primary border-b-2 border-primary bg-white'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          Moves
        </button>
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
            activeTab === 'chat'
              ? 'text-primary border-b-2 border-primary bg-white'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          Chat
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'moves' ? (
          <div className="h-full overflow-y-auto">
            <MovesTab moves={moves} />
          </div>
        ) : (
          <ChatTab />
        )}
      </div>
    </div>
  );
}

