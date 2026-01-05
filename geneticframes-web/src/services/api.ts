// geneticframes-web/src/services/api.ts
import axios from 'axios';
import type { DNAAnalysis, SpeciesSearchResponse, SpeciesResult } from '../types';

const API = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
});

export const searchSpecies = async (query: string): Promise<SpeciesSearchResponse> => {
    const response = await API.get<SpeciesSearchResponse>(`/species/search?query=${query}`);
    return response.data;
};

export const getZooExhibits = async (): Promise<Record<string, SpeciesResult[]>> => {
    const response = await API.get<Record<string, SpeciesResult[]>>('/species/exhibits');
    return response.data;
};

export const analyzeDNA = async (speciesName: string, mutationRate: number = 0): Promise<DNAAnalysis> => {
    const response = await API.post<DNAAnalysis>('/dna/analyze', {
        species_name: speciesName,
        mutation_rate: mutationRate
    });
    return response.data;
};
