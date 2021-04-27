from pathlib import Path
from arteraro.auxt.script import JobScript
from .fairseq import FairseqTrainCommand

def make_data_bins(data_path, data_indices):
    data_bin_list = [Path(data_path) / str(n) / 'data-bin' for n in data_indices]
    data_bin_list = [str(path.resolve()) for path in data_bin_list]
    data_bins = ':'.join(data_bin_list)
    return data_bins

class WorkerJobScript(JobScript):
    localdir = True

    def __init__(self, index, num_node, gpu_per_node = None, port = None):
        self.index = index
        self.num_node = num_node
        self.gpu_per_node = gpu_per_node
        self.port = port
        super().__init__()

    def make_path(self):
        return '{}/worker.sh'.format(self.index)

    def make_copy(self, data_indices):
        for index in range(len(data_indices)):
            self.append('mkdir -p ${{SGE_LOCALDIR}}/{}'.format(index))

        for n, index in enumerate(data_indices):
            data_path = Path(self.config['data']).resolve() / str(index) / 'data-bin'
            self.append('cp -r {} ${{SGE_LOCALDIR}}/{} &'.format(data_path, n))
        self.append('wait')

    def make_data_indices(self):
        data_indices = self.config['data_indices'][self.index]
        return data_indices

    def make_train_command(self, data_indices):
        data_bin = make_data_bins(self.config['data'], data_indices)
        log_file = str(Path(str(self.index)).resolve() / 'train.log')
        command = FairseqTrainCommand(data_bin, log_file)

        if 'restore_file' in self.config['train']:
            command.restore_file(str(Path(self.config['train']['restore_file'][self.index]).resolve()))

        command.seed(self.config['train']['seed_list'][self.index])
        command.log()
        command.fp16()
        if self.config.get('no_c10d', False):
            command.no_c10d()
        command.epoch(self.config['train']['max_epoch'])
        command.batch(self.config['train']['update_freq'], self.config['train']['max_tokens'])
        command.arch(
                prenorm = self.config['train'].get('prenorm', True),
                arch = self.config['train']['arch'],
                share_all_embeddings = self.config['train'].get('share_all_embeddings', True),
                dropout = self.config['train'].get('dropout', 0.3),
                attention_dropout = self.config['train'].get('attention_dropout', 0.2),
                activation_dropout = self.config['train'].get('activation_dropout', 0.2),
                activation_fn = self.config['train'].get('activation_fn', 'gelu'))
        command.adam(*self.config['train'].get('adam_betas', [0.9, 0.999]))
        command.inverse_sqrt(
                self.config['train']['lr'],
                self.config['train']['warmup_updates'],
                self.config['train'].get('warmup_init_lr', 1.0e-07))
        command.clip_norm(self.config['train'].get('clip_norm', 1.0))
        command.weight_decay(self.config['train'].get('weight_decay', 1.0e-03))
        command.label_smoothed_cross_entropy(self.config['train'].get('label_smoothing', 0.1))
        if self.num_node > 1:
            command.distributed(self.num_node, self.gpu_per_node, self.port)
        return command

    def make(self):
        data_indices = self.make_data_indices()
        if self.config['train'].get('copy_data_bin', False):
            self.make_copy(data_indices)
        command = self.make_train_command(data_indices)
        self.append(str(command))
