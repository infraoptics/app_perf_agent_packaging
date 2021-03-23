# Generated from <%= spec.file_name %> by gem2rpm -*- rpm-spec -*-
%global gem_name <%= spec.name %>

Name: rubygem-%{gem_name}
Version: <%= spec.version %>
Release: 1%{?dist}
Summary: <%= spec.summary.gsub(/\.$/, "") %>
License: <%= spec.licenses.join(" and ") %>
<% if spec.homepage -%>
URL: <%= spec.homepage %>
<% end -%>
Source0: <%= download_path %>%{gem_name}-%{version}.gem
BuildRequires: ruby(release)
<% for req in spec.required_rubygems_version -%>
BuildRequires: <%= requirement 'rubygems-devel', req %>
<% end -%>
<% for req in spec.required_ruby_version -%>
BuildRequires: <%= requirement "ruby#{'-devel' unless spec.extensions.empty?}", req %>
<% end -%>
<% unless spec.extensions.empty? -%>
# Compiler is required for build of gem binary extension.
# https://fedoraproject.org/wiki/Packaging:C_and_C++#BuildRequires_and_Requires
BuildRequires: gcc
<% end -%>
<%= development_dependencies.reject do |d|
  ["rdoc", "rake", "bundler"].include? d.name
end.virtualize.with_requires.comment_out.to_rpm -%>
<% if spec.extensions.empty? -%>
BuildArch: noarch
<% end -%>

%description
<%= spec.description %>

<% if doc_subpackage -%>
%package doc
Summary: Documentation for %{name}
Requires: %{name} = %{version}-%{release}
BuildArch: noarch

%description doc
Documentation for %{name}.
<% end # if doc_subpackage -%>

%prep
%setup -q -n %{gem_name}-%{version}

%build
# Create the gem as gem install only works on a gem file
gem build ../%{gem_name}-%{version}.gemspec

# %%gem_install compiles any C extensions and installs the gem into ./%%gem_dir
# by default, so that we can move it into the buildroot in %%install
%gem_install

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

<% unless spec.executables.empty? -%>
mkdir -p %{buildroot}%{_bindir}
cp -a .%{_bindir}/* \
        %{buildroot}%{_bindir}/

find %{buildroot}%{gem_instdir}/<%= spec.bindir %> -type f | xargs chmod a+x
<% end -%>

%check
pushd .%{gem_instdir}
<% if tests.entries.empty? -%>
# Run the test suite.
<% end -%>
<% for t in tests -%>
# <%= t.command %>
<% end -%>
popd

%files
%dir %{gem_instdir}
<% for f in spec.executables -%>
%{_bindir}/<%= f %>
<% end -%>
<% unless spec.extensions.empty? -%>
%{gem_extdir_mri}
<% end -%>
<%= main_files.reject do |item|
  spec.extensions.detect { |extension| item =~ /^#{extension.split(File::SEPARATOR).first}$/}
end.to_rpm %>
<% unless doc_subpackage -%>
%doc %{gem_docdir}
<%= doc_files.to_rpm %>
<% end -%>
%exclude %{gem_cache}
%{gem_spec}

<% if doc_subpackage -%>
%files doc
%doc %{gem_docdir}
<%= doc_files.to_rpm %>
<% end # if doc_subpackage -%>

%changelog
* <%= Time.now.strftime("%a %b %d %Y") %> <%= packager %> - <%= spec.version %>-1
- Initial package
