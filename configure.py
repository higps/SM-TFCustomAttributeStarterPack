#!/usr/bin/python

import os

# plugin names, relative to `scripting/`
plugins = [
  'airblast_projectiles_adds_self_condition.sp',
  'airblast_projectiles_restores_health.sp',
  'alt_fire_throws_cleaver.sp',
  'attr_buff_override.sp',
  'attr_group_overheal_uber.sp',
  'attr_medic_disable_active_regen.sp',
  'attr_nailgun_slow.sp',
  'attr_rage_meter_mult.sp',
  'attr_rage_on_headshot.sp',
  'attr_sapper_recharge_time.sp',
  'attr_sapper_reprograms_buildings.sp',
  'attr_weapon_always_gibs_on_kill.sp',
  'cloak_debuff_time_scale.sp',
  'condition_stack_on_hit.sp',
  'crossbow_addcond_on_teammate_hit.sp',
  'custom_drink_effect.sp',
  'damage_increase_on_hit.sp',
  'flamethrower_alt_fire_oil.sp',
  'full_clip_refill_after_time.sp',
  'generate_rage_on_dmg_patch.sp',
  'generate_rage_over_time.sp',
  'joke_medigun_mod_drain_health.sp',
  'keep_disguise_on_attack.sp',
  'lunchbox_override_pickup_type.sp',
  'minigun_burst_shot_rage.sp',
  'mod_crit_type_on_hitgroup.sp',
  'mult_basegrenade_explode_radius.sp',
  'override_building_health.sp',
  'projectile_heal_on_teammate_contact.sp',
  'projectile_override_energy_ball.sp',
]

plugins += map(lambda p: os.path.join('buff_overrides', p), [
  'buff_control_rockets.sp',
  'buff_crit_and_mark_for_death.sp',
  'sniper_rage_smokeout_spies.sp',
])

plugins += map(lambda p: os.path.join('drink_effects', p), [
  'sugar_frenzy.sp',
])

# files to copy to builddir, relative to root
copy_files = [
	'configs/customweapons/apollo_pack.cfg',
	'configs/customweapons/bonk_sugar_frenzy.cfg',
	'configs/customweapons/brainteaser.cfg',
	'configs/customweapons/classic_nailgun.cfg',
	'configs/customweapons/crop_killer.cfg',
	'configs/customweapons/der_schmerzschild.cfg',
	'configs/customweapons/essendon_eliminator.cfg',
	'configs/customweapons/joke_medick_gun.cfg',
	'configs/customweapons/magnum_opus.cfg',
	'configs/customweapons/mega_buster.cfg',
	'configs/customweapons/merasmus_stash.cfg',
	'configs/customweapons/plastic_pisstol.cfg',
	'configs/customweapons/subjugated_saboteur.cfg',
	'configs/customweapons/talos.cfg',
	
	'gamedata/tf2.cattr_starterpack.txt',
]

########################
# build.ninja script generation below.

import contextlib
import misc.ninja_syntax as ninja_syntax
import os
import sys
import argparse
import platform

parser = argparse.ArgumentParser('Configures the project.')
parser.add_argument('--spcomp-dir', help = 'Directory with the SourcePawn compiler.')

args = parser.parse_args()

print('Checking for SourcePawn compiler...')
if not args.spcomp_dir or not os.path.exists(os.path.join(args.spcomp_dir, 'spcomp.exe')):
	raise FileNotFoundError('Could not find SourcePawn compiler.')
print('Found SourcePawn compiler.')

with contextlib.closing(ninja_syntax.Writer(open('build.ninja', 'wt'))) as build:
	build.comment('This file is used to build SourceMod plugins with ninja.')
	build.comment('The file is automatically generated by configure.py')
	build.newline()
	
	vars = {
		'configure_args': sys.argv[1:],
		'root': '.',
		'builddir': 'build',
		'spcomp': os.path.join(args.spcomp_dir, 'spcomp.exe'),
		'spcflags': '-i${root}/scripting/include -h -v0'
	}
	
	for key, value in vars.items():
		build.variable(key, value)
	build.newline()
	
	build.comment("""Regenerate build files if build script changes.""")
	build.rule('configure',
			command = '${configure_env}python ${root}/configure.py ${configure_args}',
			description = 'Reconfiguring build', generator = 1)
	
	build.build('build.ninja', 'configure',
			implicit = [ '${root}/configure.py', '${root}/misc/ninja_syntax.py' ])
	build.newline()
	
	build.rule('spcomp', deps = 'msvc',
			command = '${spcomp} ${in} ${spcflags} -o ${out}',
			description = 'Compiling ${out}')
	build.newline()
	
	# Platform-specific copy instructions
	if platform.system() == "Windows":
		build.rule('copy', command = 'cmd /c copy ${in} ${out} > NUL', description = 'Copying ${out}')
	elif platform.system() == "Linux":
		build.rule('copy', command = 'cp ${in} ${out}', description = 'Copying ${out}')
	build.newline()
	
	build.comment("""Compile plugins specified in `plugins` list""")
	for plugin in plugins:
		smx_plugin = os.path.splitext(plugin)[0] + '.smx'
		
		sp_file = os.path.normpath(os.path.join('$root', 'scripting', plugin))
		
		smx_file = os.path.normpath(os.path.join('$builddir', 'plugins', 'custom-attr-starter-pack', smx_plugin))
		build.build(smx_file, 'spcomp', sp_file)
	build.newline()
	
	build.comment("""Copy plugin sources to build output""")
	for plugin in plugins:
		sp_file = os.path.normpath(os.path.join('$root', 'scripting', plugin))
		
		dist_sp = os.path.normpath(os.path.join('$builddir', 'scripting', plugin))
		build.build(dist_sp, 'copy', sp_file)
	build.newline()
	
	for filepath in copy_files:
		build.build(os.path.normpath(os.path.join('$builddir', filepath)), 'copy',
				os.path.normpath(os.path.join('$root', filepath)))
