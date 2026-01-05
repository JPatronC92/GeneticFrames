// geneticframes-web/src/types/index.ts

export interface ArtTraits {
    color_palette: string[];
    geometry_style: string;
    complexity_score: number;
    texture_type: string;
    particle_count: number;
}

export interface DNAAnalysis {
    species_name: string;
    sequence_length: number;
    gc_content: number;
    nucleotide_counts: Record<string, number>;
    sequence_preview: string;
    genomic_signature: string;
    art_traits: ArtTraits;
}

export interface SpeciesResult {
    common_name: string;
    scientific_name: string;
    confidence: number;
    source: string;
    taxonomy?: {
        group: string;
    };
}

export interface SpeciesSearchResponse {
    query: string;
    results: SpeciesResult[];
    total: number;
}
