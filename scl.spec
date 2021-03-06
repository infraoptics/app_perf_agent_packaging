# template: scl
<%-
require 'json'
root = `git rev-parse --show-toplevel`.strip
SCL_PREFIXES = JSON.load(File.read(File.join(root, 'scl_prefixes.json')))
LICENSES = JSON.load(File.read(File.join(root, 'licenses.json')))

config.rules[:doc] << /\/?CHANGES/

config.rules[:ignore] << 'Guardfile'
config.rules[:ignore] << '.document'
config.rules[:ignore] << 'Appraisals'
config.rules[:ignore] << 'gemfiles'
-%>
%{?scl:%scl_package rubygem-%{gem_name}}
%{!?scl:%global pkg_name %{name}}

%global gem_name <%= spec.name %>
%global gem_require_name %{gem_name}

Name: %{?scl_prefix}rubygem-%{gem_name}
Version: <%= spec.version %>
Release: 1%{?dist}
Summary: <%= spec.summary.gsub(/\.$/, "") %>
Group: Development/Languages
License: <%= spec.licenses.empty? ? 'FIXME' : spec.licenses.map { |l| LICENSES.fetch(l, l) }.join(" and ") %>
<% if spec.homepage -%>
URL: <%= spec.homepage %>
<% end -%>
Source0: <%= download_path %>%{gem_name}-%{version}.gem

Autoreq: 0

# start specfile generated dependencies
Requires: %{?scl_prefix_ruby}ruby(release)
<% for req in spec.required_ruby_version -%>
Requires: %{?scl_prefix_ruby}ruby <%= req %>
<% end -%>
<% for req in spec.required_rubygems_version -%>
Requires: %{?scl_prefix_ruby}ruby(rubygems) <%= req %>
<% end -%>
<% for d in spec.runtime_dependencies -%>
<% for req in d.requirement -%>
Requires: %{?scl_prefix<%= SCL_PREFIXES[d.name] %>}rubygem(<%= d.name %>) <%= req  %>
<% end -%>
<% end -%>
BuildRequires: %{?scl_prefix_ruby}ruby(release)
<% for req in spec.required_ruby_version -%>
BuildRequires: %{?scl_prefix_ruby}ruby<%= "-devel" unless spec.extensions.empty? %> <%= req %>
<% end -%>
<% for req in spec.required_rubygems_version -%>
BuildRequires: %{?scl_prefix_ruby}rubygems-devel <%= req %>
<% end -%>
<% if spec.extensions.empty? -%>
BuildArch: noarch
<% else -%>
<% for d in spec.runtime_dependencies -%>
<% for req in d.requirement -%>
BuildRequires: %{?scl_prefix<%= SCL_PREFIXES[d.name] %>}rubygem(<%= d.name %>) <%= req  %>
<% end -%>
<% end -%>
<% end -%>
Provides: %{?scl_prefix}rubygem(%{gem_name}) = %{version}
# end specfile generated dependencies

%description
<%= spec.description %>

<% if doc_subpackage -%>
%package doc
Summary: Documentation for %{pkg_name}
Group: Documentation
Requires: %{?scl_prefix}%{pkg_name} = %{version}-%{release}
BuildArch: noarch

%description doc
Documentation for %{pkg_name}.
<% end # if doc_subpackage -%>

%prep
%{?scl:scl enable %{scl} - << \EOF}
gem unpack %{SOURCE0}
%{?scl:EOF}

%setup -q -D -T -n  %{gem_name}-%{version}

%{?scl:scl enable %{scl} - << \EOF}
gem spec %{SOURCE0} -l --ruby > %{gem_name}.gemspec
%{?scl:EOF}

%build
# Create the gem as gem install only works on a gem file
%{?scl:scl enable %{scl} - << \EOF}
gem build %{gem_name}.gemspec
%{?scl:EOF}

# %%gem_install compiles any C extensions and installs the gem into ./%%gem_dir
# by default, so that we can move it into the buildroot in %%install
%{?scl:scl enable %{scl} - << \EOF}
%gem_install
%{?scl:EOF}

%install
mkdir -p %{buildroot}%{gem_dir}
cp -a .%{gem_dir}/* \
        %{buildroot}%{gem_dir}/

<% unless spec.extensions.empty? -%>
mkdir -p %{buildroot}%{gem_extdir_mri}
cp -a .%{gem_extdir_mri}/{gem.build_complete,*.so} %{buildroot}%{gem_extdir_mri}/

<% for ext in spec.extensions -%>
# Prevent dangling symlink in -debuginfo (rhbz#878863).
rm -rf %{buildroot}%{gem_instdir}/<%= ext.split(File::SEPARATOR).first %>/
<% end -%>

<% end -%>
<% unless spec.executables.nil? or spec.executables.empty? -%>
mkdir -p %{buildroot}%{_bindir}
cp -a .%{_bindir}/* \
        %{buildroot}%{_bindir}/
find %{buildroot}%{gem_instdir}/<%= spec.bindir %> -type f | xargs chmod a+x

<% end -%>
<% unless spec.extensions.empty? -%>
%check
%{?scl:scl enable %{scl} - << \EOF}
# Ideally, this would be something like this:
# GEM_PATH="%{buildroot}%{gem_dir}:$GEM_PATH" ruby -e "require '%{gem_require_name}'"
# But that fails to find native extensions on EL8, so we fake the structure that ruby expects
mkdir gem_ext_test
cp -a %{buildroot}%{gem_dir} gem_ext_test/
mkdir -p gem_ext_test/gems/extensions/%{_arch}-%{_target_os}/$(ruby -r rbconfig -e 'print RbConfig::CONFIG["ruby_version"]')/
cp -a %{buildroot}%{gem_extdir_mri} gem_ext_test/gems/extensions/%{_arch}-%{_target_os}/$(ruby -r rbconfig -e 'print RbConfig::CONFIG["ruby_version"]')/
GEM_PATH="./gem_ext_test/gems:$GEM_PATH" ruby -e "require '%{gem_require_name}'"
rm -rf gem_ext_test
%{?scl:EOF}

<% end -%>
%files
%dir %{gem_instdir}
<% unless spec.executables.nil? or spec.executables.empty? -%>
<% for f in spec.executables -%>
%{_bindir}/<%= f %>
<% end -%>
<% end -%>
<% unless spec.extensions.empty? -%>
%exclude %{gem_instdir}/ext
%{gem_extdir_mri}
<% end -%>
<%= main_file_entries(spec) %>
<% unless doc_subpackage -%>
%doc %{gem_docdir}
<%= doc_file_entries(spec) %>
<% end -%>
%exclude %{gem_cache}
%{gem_spec}

<% if doc_subpackage -%>
%files doc
%doc %{gem_docdir}
<%= doc_file_entries(spec) %>
<% end # if doc_subpackage -%>

%changelog
