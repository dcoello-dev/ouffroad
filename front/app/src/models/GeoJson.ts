export interface GeoJsonFeatureCollection {
  type: "FeatureCollection";
  features: GeoJsonFeature[];
}

export interface GeoJsonFeature {
  type: "Feature";
  geometry: {
    type: string; // e.g., "Point", "LineString", "Polygon"
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    coordinates: any[] | number[] | number[][][] | null; // More specific, but still flexible
  };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  properties: Record<string, any>; // GeoJSON properties can be anything
}
