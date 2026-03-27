import { useState, useEffect } from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';

const STACKS = [
  {
    id: 'auto',
    name: 'Auto Detect',
    description: 'Let AI choose the best stack based on your PRD',
    color: 'bg-gray-500',
  },
  {
    id: 'python',
    name: 'Python',
    description: 'Flask/FastAPI backend with SQLite',
    color: 'bg-blue-500',
  },
  {
    id: 'react',
    name: 'React',
    description: 'Next.js frontend with Tailwind CSS',
    color: 'bg-cyan-500',
  },
  {
    id: 'nodejs',
    name: 'Node.js',
    description: 'Express backend with SQLite',
    color: 'bg-green-500',
  },
];

export default function StackSelector({ onSelect, selectedStack = 'auto' }) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStack, setCurrentStack] = useState(selectedStack);

  useEffect(() => {
    setCurrentStack(selectedStack);
  }, [selectedStack]);

  const handleSelect = (stackId) => {
    setCurrentStack(stackId);
    setIsOpen(false);
    if (onSelect) {
      onSelect(stackId);
    }
  };

  const selectedStackData = STACKS.find((s) => s.id === currentStack) || STACKS[0];

  return (
    <div className="relative w-full max-w-md">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Technology Stack
      </label>
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="relative w-full bg-white border border-gray-300 rounded-lg shadow-sm pl-4 pr-10 py-3 text-left cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        >
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full ${selectedStackData.color} mr-3`} />
            <div>
              <div className="text-sm font-medium text-gray-900">
                {selectedStackData.name}
              </div>
              <div className="text-xs text-gray-500">
                {selectedStackData.description}
              </div>
            </div>
          </div>
          <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
            <ChevronDownIcon className="h-5 w-5 text-gray-400" />
          </span>
        </button>

        {isOpen && (
          <ul className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
            {STACKS.map((stack) => (
              <li
                key={stack.id}
                onClick={() => handleSelect(stack.id)}
                className="cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-gray-100"
              >
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full ${stack.color} mr-3`} />
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {stack.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {stack.description}
                    </div>
                  </div>
                </div>
                {currentStack === stack.id && (
                  <span className="absolute inset-y-0 right-0 flex items-center pr-4">
                    <svg
                      className="h-5 w-5 text-indigo-600"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}