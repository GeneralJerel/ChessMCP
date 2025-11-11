/**
 * Moves Tab Component
 * Displays move history in chess notation
 */

interface MovesTabProps {
  moves: string[];
}

export function MovesTab({ moves }: MovesTabProps) {
  // Format moves into pairs (white, black)
  const movePairs: Array<{ number: number; white: string; black?: string }> = [];
  for (let i = 0; i < moves.length; i += 2) {
    movePairs.push({
      number: Math.floor(i / 2) + 1,
      white: moves[i],
      black: moves[i + 1],
    });
  }

  return (
    <div className="p-4">
      <h3 className="font-semibold text-gray-900 mb-4">Move History</h3>
      
      {moves.length === 0 ? (
        <div className="text-center text-gray-500 mt-8">
          <p className="text-sm">No moves yet</p>
          <p className="text-xs mt-1">Make your first move to begin!</p>
        </div>
      ) : (
        <div className="space-y-1">
          {movePairs.map((pair) => (
            <div
              key={pair.number}
              className="flex items-center space-x-2 py-2 px-3 hover:bg-gray-100 rounded transition-colors"
            >
              <span className="text-sm font-medium text-gray-600 w-8">
                {pair.number}.
              </span>
              <span className="text-sm font-mono text-gray-900 w-16">
                {pair.white}
              </span>
              {pair.black && (
                <span className="text-sm font-mono text-gray-900 w-16">
                  {pair.black}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {moves.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-xs text-gray-600">
            Total moves: {moves.length}
          </p>
        </div>
      )}
    </div>
  );
}

