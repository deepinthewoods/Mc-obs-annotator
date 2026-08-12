import React from 'react';

interface EventStatisticsProps {
  statistics: { [key: string]: number };
  totalCount: number;
}

const EVENT_TYPE_PREFIX_COLORS: [string, string][] = [
  ['Combat', '🔴'],
  ['Entity Attacked', '🔴'],
  ['Damage', '🔴'],
  ['Boss', '🟣'],
  ['Block Break', '🔵'],
  ['Block Place', '🔵'],
  ['Rare Item', '🟢'],
  ['Food Eaten', '🟢'],
  ['Potion Drunk', '🟢'],
  ['Bow Fired', '🟢'],
  ['Crossbow Fired', '🟢'],
  ['Trident Thrown', '🟢'],
  ['Ender Pearl', '🟢'],
  ['Item Used', '🟢'],
  ['Item - Tool Broke', '🟢'],
  ['Exploration', '🔵'],
  ['Achievement', '🟡'],
  ['Fall Landed', '🟤'],
  ['Elytra', '🟤'],
  ['Mount', '🟤'],
  ['Explosion', '🟠'],
  ['Environment', '🟠'],
  ['Crafted', '🟡'],
  ['Trade', '🟡'],
  ['Enchanted', '🟡'],
  ['Interaction', '🟡'],
  ['Entered', '🟣'],
  ['Returned', '🟣'],
  ['Started Sleeping', '🔵'],
  ['Woke Up', '🔵'],
  ['Status Effect', '🟢'],
  ['Manual', '🟡'],
];

function getEventColor(eventType: string): string {
  for (const [prefix, color] of EVENT_TYPE_PREFIX_COLORS) {
    if (eventType.startsWith(prefix)) return color;
  }
  return '⚪';
}

export const EventStatistics: React.FC<EventStatisticsProps> = ({
  statistics,
  totalCount,
}) => {
  const entries = Object.entries(statistics).sort((a, b) => b[1] - a[1]);

  return (
    <div className="event-statistics">
      <h2>📊 Event Statistics</h2>
      <div className="statistics-grid">
        {entries.map(([type, count]) => (
          <div key={type} className="stat-item">
            {getEventColor(type)} {type}: {count}
          </div>
        ))}
        {entries.length > 0 && (
          <div className="stat-item total">
            Total: {totalCount}
          </div>
        )}
      </div>
    </div>
  );
};
