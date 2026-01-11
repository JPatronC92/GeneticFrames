// geneticframes-web/src/pages/SpeciesArt.tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyzeDNA } from '@services/api';
import { useRoute } from 'wouter';
import DNAFrame from '@components/dna/DNAFrame';
import { Dna, RefreshCw, ArrowLeft, FlaskConical } from 'lucide-react';
import { Link } from 'wouter';

export const SpeciesArt = () => {
    const [, params] = useRoute('/species/:name');
    const speciesName = decodeURIComponent(params?.name || '');
    const [mutationRate, setMutationRate] = useState(0);

    const { data, isLoading } = useQuery({
        queryKey: ['dna', speciesName, mutationRate],
        queryFn: () => analyzeDNA(speciesName, mutationRate),
        enabled: !!speciesName
    });

    const handleMutate = () => {
        // Increase mutation slightly
        setMutationRate(prev => Math.min(prev + 0.05, 1.0));
    };

    const handleReset = () => {
        setMutationRate(0);
    };

    if (isLoading) return (
        <div className="min-h-screen bg-dna-dark flex items-center justify-center text-white">
            <div className="text-center">
                <Dna className="animate-spin h-12 w-12 mx-auto mb-4 text-dna-accent" />
                <p>Sequencing DNA...</p>
            </div>
        </div>
    );

    if (!data) return <div className="text-white">Not found</div>;

    return (
        <div className="min-h-screen bg-dna-dark text-white p-4 md:p-8">
            <Link href="/">
                <a className="inline-flex items-center text-gray-400 hover:text-white mb-6 transition-colors">
                    <ArrowLeft size={20} className="mr-2" /> Back to Zoo
                </a>
            </Link>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
                {/* Left Panel: Info & Stats */}
                <div className="lg:col-span-1 space-y-6">
                    <div>
                        <h1 className="text-4xl font-bold mb-2 text-dna-accent">{data.species_name}</h1>
                        <p className="text-gray-400 font-mono text-sm break-all">
                            ID: {data.genomic_signature.substring(0, 16)}...
                        </p>
                    </div>

                    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 space-y-4">
                        <h3 className="font-semibold text-lg flex items-center">
                            <Dna size={20} className="mr-2 text-purple-400" /> Genetic Stats
                        </h3>
                        <div className="space-y-2 text-sm text-gray-300">
                            <div className="flex justify-between">
                                <span>Length</span>
                                <span className="font-mono">{data.sequence_length} bp</span>
                            </div>
                            <div className="flex justify-between">
                                <span>GC Content</span>
                                <span className="font-mono">{data.gc_content.toFixed(2)}%</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Complexity</span>
                                <span className="font-mono">{data.art_traits.complexity_score}</span>
                            </div>
                        </div>

                        {/* Nucleotide Bar */}
                        <div className="flex h-4 rounded-full overflow-hidden mt-4">
                            <div style={{ width: `${(data.nucleotide_counts.A / data.sequence_length) * 100}%` }} className="bg-green-500" title="A" />
                            <div style={{ width: `${(data.nucleotide_counts.T / data.sequence_length) * 100}%` }} className="bg-red-500" title="T" />
                            <div style={{ width: `${(data.nucleotide_counts.G / data.sequence_length) * 100}%` }} className="bg-yellow-500" title="G" />
                            <div style={{ width: `${(data.nucleotide_counts.C / data.sequence_length) * 100}%` }} className="bg-blue-500" title="C" />
                        </div>
                    </div>

                    {/* Mutation Controls */}
                    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 border-l-4 border-l-pink-600">
                        <h3 className="font-semibold text-lg mb-4 flex items-center text-pink-400">
                            <FlaskConical size={20} className="mr-2" /> Evolution Lab
                        </h3>
                        <p className="text-sm text-gray-400 mb-4">
                            Simulate genetic drift and observe how the artwork evolves.
                        </p>

                        <div className="flex items-center gap-4 mb-4">
                            <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-pink-500 transition-all duration-500"
                                    style={{ width: `${mutationRate * 100}%` }}
                                />
                            </div>
                            <span className="font-mono text-pink-300">{(mutationRate * 100).toFixed(0)}%</span>
                        </div>

                        <div className="flex gap-2">
                            <button
                                onClick={handleMutate}
                                className="flex-1 bg-pink-600 hover:bg-pink-700 text-white py-2 rounded-lg font-medium transition-colors"
                            >
                                Mutate DNA
                            </button>
                            {mutationRate > 0 && (
                                <button
                                    onClick={handleReset}
                                    className="px-4 border border-gray-600 hover:bg-gray-800 rounded-lg"
                                    title="Reset to wild type"
                                >
                                    <RefreshCw size={18} />
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Panel: The Art */}
                <div className="lg:col-span-2">
                    <div className="bg-gray-900 rounded-xl border border-gray-800 p-2 shadow-2xl shadow-blue-900/10">
                         <DNAFrame traits={data.art_traits} />
                    </div>

                    <div className="mt-6 font-mono text-xs text-gray-600 break-all p-4 bg-black rounded border border-gray-900">
                        {data.sequence_preview}
                    </div>
                </div>
            </div>
        </div>
    );
};
