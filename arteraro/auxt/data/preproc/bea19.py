from pathlib import Path
from arteraro.auxt.util.load import load_config, check_sub_config
from .job import PreprocessJobScript
from .run import PreprocessRunScript
from .sub import PreprocessSubScript
from .fairseq import fairseq_preprocess_command

class BEA19PreprocessJobScript(PreprocessJobScript):
    def make(self):
        if ('preprocess' in self.config) and ('prepared' in self.config['preprocess']):
            base_path = Path(self.config['preprocess']['prepared']) / str(self.index)
        else:
            base_path = Path(str(self.index))
        compressed_source = str((base_path / 'train.src.gz').resolve())
        compressed_target = str((base_path / 'train.trg.gz').resolve())
        extracted_source = '${SGE_LOCALDIR}/train.src'
        extracted_target = '${SGE_LOCALDIR}/train.trg'

        self.append('zcat {} > {} &'.format(compressed_source, extracted_source))
        self.append('zcat {} > {} &'.format(compressed_target, extracted_target))
        self.append('wait')
        self.append('')

        train_pref = '${SGE_LOCALDIR}/train'
        valid_pref = Path(self.config['dataset']['valid_pref']).resolve()

        dest_dir = Path('{}/data-bin'.format(self.index)).resolve()
        threads = self.config['threads']

        source_lang = 'src'
        target_lang = 'trg'
        src_dict = self.make_dict_path(source_lang)
        trg_dict = None
        if 'preprocess' in self.config:
            joined_dict = self.config['preprocess'].get('joined_dict', True)
        else:
            joined_dict = True
        command = fairseq_preprocess_command(
                source_lang,
                target_lang,
                train_pref,
                valid_pref,
                dest_dir,
                threads,
                src_dict = src_dict,
                trg_dict = trg_dict,
                joined_dict = joined_dict)
        self.append(command)


def bea19_preproc():
    config = load_config()
    num_iter = config['iter']

    if 'preprocess' in config:
        if 'src_dict_path' in config['preprocess']:
            first_index = None
        else:
            first_index = config['preprocess'].get('first_index', 0)
    else:
        first_index = 0

    if first_index is not None:
        first_script = BEA19PreprocessJobScript(first_index, first_index)
    script_list = [BEA19PreprocessJobScript(first_index, n)
            for n in range(num_iter)
            if n != first_index]

    if check_sub_config():
        if first_index is not None:
            first_sub = PreprocessSubScript([first_script], first=True)
        rest_sub = PreprocessSubScript(script_list)
    else:
        if first_index is not None:
            first_run = PreprocessRunScript([first_script], first=True)
        rest_run = PReprocessRunScript(script_list)

