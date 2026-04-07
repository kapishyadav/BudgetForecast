from sentence_transformers import SentenceTransformer, util
import torch

class SemanticColumnMapper:
    _instance = None

    def __new__(cls):
        # Singleton pattern ensures the model is only loaded once in memory
        if cls._instance is None:
            cls._instance = super(SemanticColumnMapper, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Loads the model and pre-computes the target embeddings on startup.
        all-MiniLM-L6-v2 is fast, lightweight (under 100MB), and excellent for semantic text similarity.
        """
        print("Loading MiniLM model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        # 1. Define your strict internal schema
        self.internal_columns = [
            'date',
            'spend',
            'accountName',
            'serviceName',
            'buCode',
            'segment'
        ]

        # 2. Pre-compute the embeddings for your internal columns
        # convert_to_tensor=True keeps it on the GPU (if available) or fast CPU tensors
        self.internal_embeddings = self.model.encode(
            self.internal_columns,
            convert_to_tensor=True
        )
        print("Internal embeddings pre-computed.")

    def map_columns(self, user_columns: list[str], threshold: float = 0.75) -> dict:
        """
        Takes a list of unrecognized user column names and attempts to map them.
        """
        if not user_columns:
            return {}

        # 3. Embed the user's incoming columns
        user_embeddings = self.model.encode(user_columns, convert_to_tensor=True)

        # 4. Calculate cosine similarity between all user columns and all internal columns at once
        # This creates a matrix of scores: [len(user_columns) x len(internal_columns)]
        cosine_scores = util.cos_sim(user_embeddings, self.internal_embeddings)

        mapping_results = {}

        # 5. Iterate through the results and apply the threshold
        for i, user_col in enumerate(user_columns):
            # Find the index of the highest score for this user column
            best_match_idx = torch.argmax(cosine_scores[i]).item()
            best_score = cosine_scores[i][best_match_idx].item()

            if best_score >= threshold:
                mapping_results[user_col] = {
                    "mapped_to": self.internal_columns[best_match_idx],
                    "confidence": round(best_score, 4),
                    "status": "mapped"
                }
            else:
                mapping_results[user_col] = {
                    "mapped_to": None,
                    "confidence": round(best_score, 4),
                    "status": "unmapped"
                }

        return mapping_results