from pathlib import Path

from ffopt.jobs.utils import replace_placeholders
from ffopt.parsers.cif import ParserCif


class GulpJob():
    def __init__(self, system: dict, gulp_settings: dict, ff_template: str):
        self.data = system
        self.gulp_settings = gulp_settings
        self.ff_template = ff_template

    # Головной метод
    def generate_input(self, values: dict) -> str:
        "Method for generation input files for GULP."
        if structure := self.data.get('calc_template'):
            return replace_placeholders(structure, values)
        elif self.data['structure'].endswith('.cif'):
            parser = ParserCif(Path(self.data['structure']))
            parser.parse()
            # TODO Нужно брать опцию из инпут файла, а эту использовать по дефолту
            structure = parser.data['gulp_only_core_structure']
        elif structure := self.data['structure']:
            structure = structure
        else:
            ValueError(f"Cannot find structure in {self.data}")
        
        header = self._generate_header()
        settings = self._generate_settings()
        other = self._generate_other()
        ff = self._generate_ff(values)

        gin = '\n'.join([header, settings, structure, other, ff])
        return gin

    def _generate_header(self):
        header = 'optimise c6 conp comp property '
        if 'kpoints_values' in self.data:
            header += 'phonon nononanal'
        return header.strip()

    def _generate_settings(self):
        settings = ''
        for setting in self.gulp_settings:
            if (setting == 'path') or (setting == 'software'):
                continue
            else:
                settings += f'{setting} {self.gulp_settings[setting]}\n'
        return settings.strip()

    def _generate_other(self):
        other = ''
        # SShift
        if sshift := self.data.get('sshift'):
            other += f'sshift {sshift}\n'
        # kpoints
        if k_points := self.data.get('kpoints_index'):
            other += f'kpoints {len(k_points)}\n'
            for point in k_points:
                other += ' '.join(str(i) for i in point) 
                other += '\n'

        return other.strip()

    def _generate_ff(self, values):
        return replace_placeholders(self.ff_template, values)