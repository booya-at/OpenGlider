import pandas as pd


def to_df(the_list):
    df_list = []
    for obj in the_list:
        obj_dict = obj.__json__()
        obj_dict["obj"] = obj
        df_list.append(obj_dict)


def apply_df(df):
    assert "obj" in df.columns
    objs_dict = df.to_dict("records")
    for obj_dict in objs_dict:
        obj = obj_dict.pop("obj")
        # apply the attributes?
