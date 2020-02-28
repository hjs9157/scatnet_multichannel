#!/usr/bin/sh
# submits jobs to the cluster using list of hyperparameters in the params.csv file.
# two queues exist: the cluster queue and the parameters queue. 
# for job submission to the cluster I term it enqueue for the cluster, 
# and adding new sets of hyperparameters to params.csv I term it enqueue for the parameters.
# using crontab, the queue status on the cluster is checked to see if additional jobs can be submitted

SCATNET_DIR="/nobackup/users/yoonjung/repos/scatnet_multichannel"
cd ${SCATNET_DIR}

# job count
N_JOBS_MAX=4
# the "No unfinished jobs" is an error message and therefore does not count in wc -l
# FIXME: however there's a header row when there are jobs. So if N_JOBS_SUBMITTED becomes -1, set it to 0
N_JOBS_SUBMITTED=$(expr $(bjobs 2>/dev/null | wc -l) - 1) 
FILE_NAME_PARAMS="params.csv"
SLEEP_TIME=0
while [[ "${N_JOBS_SUBMITTED}" -lt "${N_JOBS_MAX}" ]] && [ -s "${FILE_NAME_PARAMS}" ]
do
    # read parameters 1 line at a time
    head -n 1 "${FILE_NAME_PARAMS}" | while IFS=, read \
        FILE_NAME \
        ROOT_DIR \
        HIDDEN_SIZE \
        N_LAYERS \
        BIDIRECTIONAL \
        CLASSIFIER \
        IDX_LABEL \
        EPOCHS \
        TRAIN_RATIO \
        BATCH_SIZE \
        N_WORKERS \
        LR \
        BETAS \
        OPT_LEVEL \
        SEED \
        LOG_INTERVAL
    do
        # text substitution using the template
        cat rnn_template.lsf | sed \
            -e "s/<FILE_NAME>/${FILE_NAME}/g" \
            -e "s|<ROOT_DIR>|${ROOT_DIR}|g" \
            -e "s/<HIDDEN_SIZE>/${HIDDEN_SIZE}/g" \
            -e "s/<N_LAYERS>/${N_LAYERS}/g" \
            -e "s/<BIDIRECTIONAL>/${BIDIRECTIONAL}/g" \
            -e "s/<CLASSIFIER>/${CLASSIFIER}/g" \
            -e "s/<IDX_LABEL>/${IDX_LABEL}/g" \
            -e "s/<EPOCHS>/${EPOCHS}/g" \
            -e "s/<TRAIN_RATIO>/${TRAIN_RATIO}/g" \
            -e "s/<BATCH_SIZE>/${BATCH_SIZE}/g" \
            -e "s/<N_WORKERS>/${N_WORKERS}/g" \
            -e "s/<LR>/${LR}/g" \
            -e "s/<BETAS>/${BETAS}/g" \
            -e "s/<OPT_LEVEL>/${OPT_LEVEL}/g" \
            -e "s/<SEED>/${SEED}/g" \
            -e "s/<LOG_INTERVAL>/${LOG_INTERVAL}/g" \
            > rnn.lsf

        # submit the job
        bsub < rnn.lsf
        sed -i 1d "${FILE_NAME_PARAMS}"
    done
    # the following line should be outside the inner loop for condition check
    N_JOBS_SUBMITTED=`expr ${N_JOBS_SUBMITTED} + 1` 
    sleep ${SLEEP_TIME}
done
