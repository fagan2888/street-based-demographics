import random
import numpy as np
import pandas as pd

def permute_houses(dem_data, seed=1234):
    """
    Randomly permute houses within each block. This allows for
    an empirical distribution to test the hypothesis that data are
    clustered by street.

    Parameters
    ----------
    dem_data: pd DataFrame
            demographic (or synthetic) data with columns for TLIDs and
            BLKIDs. Each row represents a MAFID-indexed household.
    seed: int
            random seed for permutation

    Returns
    -------
    dem_data: pd DataFrame
            demographic (or synthetic) data with columns for TLIDs and
            BLKIDs. Each row represents a MAFID-indexed household. New column
            with shuffled TLIDs, called 'TLID_permuted_{iteration}'
    """
    random.seed(seed)
    dem_data['TLID_permuted_'+str(seed)] = dem_data.groupby('BLKID')['TLID'].transform(np.random.permutation)
    return dem_data


def average_pvals(pval_df, iterations=10):
    """
    Averages p-values accross several iterations

    Parameters
    ----------
    pval_df: pd DataFrame
            each row is a TLID-BLKID pair, first columns are the differences in
            aggregation for each variable, remaining columns are empirical p-values
            with a suffix of the iteration number
    iterations: int
            number of times to shuffle households and reaggregate

    Returns
    -------
    pval_df: pd DataFrame
            each row is a TLID-BLKID pair, first columns are the differences in
            aggregation for each variable, remaining columns are empirical p-values
            averaged over all iterations
    """
    for col in ['A', 'B', 'C', 'D', 'E']:
        p_val_cols = [(col+'_p_'+str(i)) for i in range(iterations)]
        these_p_vals = pval_df[p_val_cols]
        avg_col_name = col+'_avg_p'
        pval_df[avg_col_name] = these_p_vals.astype(float).mean(axis=1)
        pval_df.drop(p_val_cols, axis=1, inplace=True)

    return pval_df


def find_p_vals(data, iterations=10):
    """
    Randomly shuffles TLID assignments within each block,
    reassigning them to each MAFID. Aggregates both the true data
    and the shuffled data, and uses random shuffle to calculate
    empirical p-values for the null hypothesis of random distribution
    within blocks.

    Parameters
    ----------
    data: pd DataFrame
            demographic (or synthetic) data with columns for TLIDs and
            BLKIDs. Each row represents a MAFID-indexed household.
    iterations: int
            number of times to shuffle households and reaggregate

    Returns
    -------
    aggs_avg: pd DataFrame
            each row is a TLID-BLKID pair, first columns are the differences in
            aggregation for each variable, remaining columns are empirical p-values
            averaged over all iterations
    """

    # Aggregate "data"
    # TODO: Change this aggregation to account for real data (TLID-BLKID differences)
    aggs = data[['TLID','A', 'B', 'C', 'D', 'E']].groupby(['TLID']).mean()

    for i in range(iterations):
        shuffled_data = permute_houses(data, seed=i)
        synth_aggs = shuffled_data[['TLID_permuted_'+str(i),'A', 'B', 'C', 'D', 'E']].groupby(['TLID_permuted_'+str(i)]).mean()
        for col in ['A', 'B', 'C', 'D', 'E']:
            aggs.loc[:, col+'_p_'+str(i)] = synth_aggs[synth_aggs.abs()[col] > aggs.abs()[col]].shape[0] / synth_aggs.shape[0]

    aggs_avg = average_pvals(pval_df=aggs, iterations=iterations)
    return aggs_avg


if __name__ == "__main__":
    # Load public addresses & crosswalk
    addresses = pd.read_csv('../data/addresses/08031_addresses.csv')
    xwalk = pd.read_csv('../results/address_tlid_xwalk/08031_tlid_match.csv')
    merged_xwalk = pd.merge(addresses, xwalk, on='MAFID')
    merged_xwalk.rename(columns={'TLID_match':'TLID'}, inplace=True)

    # Create random data and merge it to address-xwalk table
    column_names = ['A', 'B', 'C', 'D', 'E']
    rand_data = pd.DataFrame(np.random.randn(merged_xwalk.shape[0], 5), columns=column_names)
    rand_data.loc[:,'MAFID'] = merged_xwalk['MAFID']
    synth_dem_data = pd.merge(merged_xwalk, rand_data, on='MAFID')

    print("\n\nSynthetic demographic data:")
    print(synth_dem_data.head())

    pvals = find_p_vals(synth_dem_data, iterations=3)
    print("\n\nP-values:")
    print(pvals.head())
