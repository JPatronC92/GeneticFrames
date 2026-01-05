// geneticframes-web/src/pages/Home.tsx
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getZooExhibits } from '../services/api';
import { useLocation } from 'wouter';
import { Search, Loader2 } from 'lucide-react';

export const Home = () => {
    const [query, setQuery] = useState('');
    const [, setLocation] = useLocation();

    // Fetch exhibits for the "Zoo Map" feel
    const { data: exhibits, isLoading } = useQuery({
        queryKey: ['exhibits'],
        queryFn: getZooExhibits
    });

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.length > 2) {
            setLocation(`/species/${query}`);
        }
    };

    return (
        <div className="min-h-screen bg-dna-dark text-white p-8">
            <header className="mb-12 text-center">
                <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mb-4">
                    GeneticFrames Zoo
                </h1>
                <p className="text-gray-400 text-lg">
                    Discover the Art hidden in DNA.
                </p>
            </header>

            {/* Search Bar */}
            <div className="max-w-2xl mx-auto mb-16 relative">
                <form onSubmit={handleSearch} className="relative">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search for a species (e.g., Tiger, Whale)..."
                        className="w-full px-6 py-4 bg-gray-900 border border-gray-700 rounded-full text-lg focus:outline-none focus:ring-2 focus:ring-dna-accent pl-14"
                    />
                    <Search className="absolute left-5 top-1/2 transform -translate-y-1/2 text-gray-500" size={24} />
                    <button
                        type="submit"
                        className="absolute right-2 top-2 bottom-2 bg-dna-accent hover:bg-blue-400 text-black font-bold px-6 rounded-full transition-colors"
                    >
                        Explore
                    </button>
                </form>
            </div>

            {/* Exhibits Grid */}
            {isLoading ? (
                <div className="flex justify-center"><Loader2 className="animate-spin" /></div>
            ) : (
                <div className="max-w-7xl mx-auto">
                    <h2 className="text-2xl font-semibold mb-8 border-b border-gray-800 pb-2">Current Exhibits</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {exhibits && Object.entries(exhibits).map(([zone, species]) => (
                            <div key={zone} className="bg-gray-900/50 p-6 rounded-xl border border-gray-800 hover:border-dna-accent transition-all group">
                                <h3 className="text-xl font-bold text-dna-accent mb-4 group-hover:text-white transition-colors">
                                    {zone}
                                </h3>
                                <ul className="space-y-2">
                                    {species.map(s => (
                                        <li
                                            key={s.scientific_name}
                                            onClick={() => setLocation(`/species/${s.common_name}`)}
                                            className="cursor-pointer hover:text-blue-300 flex justify-between text-sm text-gray-400"
                                        >
                                            <span>{s.common_name}</span>
                                            <span className="italic opacity-50">{s.scientific_name}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
