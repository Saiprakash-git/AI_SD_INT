import os
import kagglehub
import pandas as pd
import json

path = kagglehub.dataset_download("pavellexyr/the-reddit-dataset-dataset")

posts_path = os.path.join(path, "the-reddit-dataset-dataset-posts.csv")
comments_path = os.path.join(path, "the-reddit-dataset-dataset-comments.csv")

posts_df = pd.read_csv(posts_path, nrows=1)
comments_df = pd.read_csv(comments_path, nrows=1)

output = {
    "posts_cols": list(posts_df.columns),
    "comments_cols": list(comments_df.columns),
    "post_row": posts_df.head(1).to_dict('records')[0],
    "comment_row": comments_df.head(1).to_dict('records')[0]
}

with open("kaggle_schema.json", "w") as f:
    json.dump(output, f, indent=2)
